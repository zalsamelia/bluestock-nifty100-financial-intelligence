"""
Peer Comparison Analytics & Percentile Ranking Engine (Sprint 3 — Day 18).
Computes PERCENT_RANK (0.0 to 1.0) for 10 key metrics within each of 11 peer groups.
Inverts D/E percentile rank so lower debt yields a higher percentile rank.
Populates the peer_percentiles table in SQLite database.
Gracefully handles unassigned companies with 'No peer group assigned' status.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "nifty100.db"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx"

# 10 Key Metrics to rank within peer groups
RANKING_METRICS = [
    "return_on_equity_pct",
    "roce_pct",
    "net_profit_margin_pct",
    "debt_to_equity",  # Inverted (lower D/E = higher rank)
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]


def load_peer_groups_mapping(excel_path: Path = PEER_GROUPS_PATH) -> pd.DataFrame:
    """Load peer groups mapping from excel file."""
    if not excel_path.exists():
        raise FileNotFoundError(f"Peer groups excel file not found at: {excel_path}")
    df = pd.read_excel(excel_path)
    return df[["peer_group_name", "company_id", "is_benchmark"]].copy()


def migrate_peer_percentiles_table(conn: sqlite3.Connection) -> None:
    """Recreate peer_percentiles table in SQLite."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS peer_percentiles")
    cursor.execute("""
        CREATE TABLE peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER NOT NULL,
            PRIMARY KEY (company_id, peer_group_name, metric, year),
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_peer_percentiles_group
            ON peer_percentiles(peer_group_name, metric)
    """)
    conn.commit()


def compute_peer_percentiles(
    db_path: Path = DB_PATH,
    excel_path: Path = PEER_GROUPS_PATH,
    target_year: int = 2024
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Compute intra-group PERCENT_RANK for 10 metrics across 11 peer groups.
    Returns (percentile_df, unassigned_messages).
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Load financial ratios & companies
    ratios_df = pd.read_sql_query(
        "SELECT * FROM financial_ratios WHERE year = ?",
        conn,
        params=(target_year,)
    )
    if ratios_df.empty:
        max_yr = pd.read_sql_query("SELECT MAX(year) FROM financial_ratios", conn).iloc[0, 0]
        ratios_df = pd.read_sql_query(
            "SELECT * FROM financial_ratios WHERE year = ?",
            conn,
            params=(max_yr,)
        )
        target_year = int(max_yr)

    companies_df = pd.read_sql_query("SELECT company_id FROM companies", conn)
    conn.close()

    # Load peer group mappings
    peer_map_df = load_peer_groups_mapping(excel_path)
    all_companies = set(companies_df["company_id"])
    peer_companies = set(peer_map_df["company_id"])

    # Identify unassigned companies
    unassigned_ids = sorted(list(all_companies - peer_companies))
    unassigned_messages = [
        {"company_id": cid, "status": "No peer group assigned"}
        for cid in unassigned_ids
    ]

    # Merge ratios with peer groups
    merged = peer_map_df.merge(ratios_df, on="company_id", how="inner")

    percentile_records = []

    for peer_group_name, group_df in merged.groupby("peer_group_name"):
        group_df = group_df.copy()
        n_comps = len(group_df)

        for metric in RANKING_METRICS:
            if metric not in group_df.columns:
                continue

            vals = group_df[metric].values
            valid_mask = pd.notnull(group_df[metric])
            
            # Compute PERCENT_RANK (0.0 to 1.0)
            ranks = pd.Series(index=group_df.index, dtype=float)
            
            if valid_mask.sum() > 1:
                # pandas rank method='min' pct=True gives 0 to 1 percentile rank
                raw_rank = group_df.loc[valid_mask, metric].rank(method="average", pct=True)
                
                # Invert D/E percentile rank so lower D/E = higher percentile rank
                if metric == "debt_to_equity":
                    # For D/E: lower is better -> inverse percentile rank
                    inverted_rank = 1.0 - raw_rank
                    ranks.loc[valid_mask] = inverted_rank
                else:
                    ranks.loc[valid_mask] = raw_rank
            elif valid_mask.sum() == 1:
                ranks.loc[valid_mask] = 1.0  # Single valid company gets 1.0

            for idx, row in group_df.iterrows():
                cid = row["company_id"]
                val = row[metric]
                p_rank = ranks.loc[idx]

                percentile_records.append({
                    "company_id": cid,
                    "peer_group_name": peer_group_name,
                    "metric": metric,
                    "value": float(val) if pd.notna(val) else None,
                    "percentile_rank": float(p_rank) if pd.notna(p_rank) else None,
                    "year": target_year
                })

    percentile_df = pd.DataFrame(percentile_records)
    return percentile_df, unassigned_messages


def populate_peer_percentiles_table(
    db_path: Path = DB_PATH,
    excel_path: Path = PEER_GROUPS_PATH,
    target_year: int = 2024
) -> Tuple[int, int]:
    """
    Populate SQLite peer_percentiles table with computed percentile rankings.
    Returns (inserted_row_count, unassigned_company_count).
    """
    percentile_df, unassigned_messages = compute_peer_percentiles(
        db_path=db_path,
        excel_path=excel_path,
        target_year=target_year
    )

    conn = sqlite3.connect(str(db_path))
    migrate_peer_percentiles_table(conn)

    cursor = conn.cursor()
    inserted = 0
    for rec in percentile_df.to_dict(orient="records"):
        cursor.execute("""
            INSERT OR REPLACE INTO peer_percentiles (
                company_id, peer_group_name, metric, value, percentile_rank, year
            ) VALUES (
                :company_id, :peer_group_name, :metric, :value, :percentile_rank, :year
            )
        """, rec)
        inserted += 1

    conn.commit()
    conn.close()

    return inserted, len(unassigned_messages)


def get_company_peer_rankings(
    company_id: str,
    db_path: Path = DB_PATH,
    excel_path: Path = PEER_GROUPS_PATH
) -> Dict[str, Any]:
    """
    Retrieve peer rankings for a specific company.
    If company has no peer group, returns status 'No peer group assigned'.
    """
    peer_map_df = load_peer_groups_mapping(excel_path)
    comp_peer = peer_map_df[peer_map_df["company_id"] == company_id]

    if comp_peer.empty:
        return {
            "company_id": company_id,
            "status": "No peer group assigned",
            "peer_group_name": None,
            "rankings": {}
        }

    peer_group_name = comp_peer.iloc[0]["peer_group_name"]
    is_benchmark = bool(comp_peer.iloc[0]["is_benchmark"])

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT metric, value, percentile_rank
        FROM peer_percentiles
        WHERE company_id = ?
    """, (company_id,)).fetchall()
    conn.close()

    rankings = {r["metric"]: {"value": r["value"], "percentile_rank": r["percentile_rank"]} for r in rows}

    return {
        "company_id": company_id,
        "status": "Assigned",
        "peer_group_name": peer_group_name,
        "is_benchmark": is_benchmark,
        "rankings": rankings
    }
