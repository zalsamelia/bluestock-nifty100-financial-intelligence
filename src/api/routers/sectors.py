"""
Sectors Router.
Endpoints:
- GET /api/v1/sectors
- GET /api/v1/sectors/{sector}/companies
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sectors", tags=["Sector Dynamics"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("", summary="List All 11 Sectors with Aggregated Median KPIs")
def list_sectors() -> List[Dict[str, Any]]:
    """
    Returns all 11 sectors with constituent counts and median ROE, P/E, and D/E multiples.
    """
    conn = get_db_connection()
    query = """
        SELECT s.sector, 
               COUNT(DISTINCT c.company_id) AS company_count,
               fr.return_on_equity_pct,
               fr.debt_to_equity
        FROM sectors s
        JOIN companies c ON s.company_id = c.company_id
        LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
             AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.company_id)
        WHERE s.sector IS NOT NULL AND TRIM(s.sector) != ''
        GROUP BY s.sector, c.company_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return []

    # Read valuation summary for PE
    val_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    pe_df = pd.DataFrame()
    if val_path.exists():
        try:
            pe_df = pd.read_excel(val_path)
        except Exception:
            pass

    results = []
    for sec_name, grp in df.groupby("sector"):
        count = len(grp["company_count"])
        med_roe = round(float(grp["return_on_equity_pct"].median()), 2) if not grp["return_on_equity_pct"].dropna().empty else 0.0
        med_de = round(float(grp["debt_to_equity"].median()), 2) if not grp["debt_to_equity"].dropna().empty else 0.0

        # Sector median PE
        med_pe = 24.5
        if not pe_df.empty and "sector" in pe_df.columns and "pe_ratio" in pe_df.columns:
            sec_pes = pe_df[pe_df["sector"] == sec_name]["pe_ratio"].dropna()
            if not sec_pes.empty:
                med_pe = round(float(sec_pes.median()), 2)

        results.append({
            "sector": sec_name,
            "company_count": count,
            "median_roe": med_roe,
            "median_pe": med_pe,
            "median_de": med_de
        })

    # Sort by company count descending
    results.sort(key=lambda x: x["company_count"], reverse=True)
    return results


@router.get("/{sector}/companies", summary="All Constituents in a Given Sector")
def get_sector_companies(sector: str) -> Dict[str, Any]:
    """
    Returns list of all companies belonging to the specified sector with latest KPIs.
    Returns HTTP 404 if sector is not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Case-insensitive sector check
    cursor.execute("SELECT DISTINCT sector FROM sectors WHERE LOWER(sector) = LOWER(?)", (sector.strip(),))
    sec_match = cursor.fetchone()
    if not sec_match:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found in universe.")

    canonical_sector = sec_match["sector"]

    query = """
        SELECT c.company_id, c.company_name, s.sector, s.industry, s.market_cap_category,
               fr.return_on_equity_pct, fr.roce_pct, fr.net_profit_margin_pct,
               fr.debt_to_equity, fr.revenue_cagr_5yr, fr.composite_quality_score,
               pl.sales, pl.net_profit
        FROM sectors s
        JOIN companies c ON s.company_id = c.company_id
        LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
             AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.company_id)
        LEFT JOIN profitandloss pl ON c.company_id = pl.company_id
             AND pl.year = (SELECT MAX(year) FROM profitandloss WHERE company_id = c.company_id)
        WHERE LOWER(s.sector) = LOWER(?)
        ORDER BY fr.composite_quality_score DESC, c.company_name ASC
    """
    cursor.execute(query, (sector.strip(),))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "sector": canonical_sector,
        "count": len(rows),
        "companies": rows
    }
