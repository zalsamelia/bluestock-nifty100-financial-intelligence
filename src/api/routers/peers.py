"""
Peers Router.
Endpoint: GET /api/v1/peers/{group_name}
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/peers", tags=["Peer Benchmarking"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/{group_name}", summary="Peer Group Ranking & Percentile Matrices")
def get_peer_group_details(group_name: str) -> Dict[str, Any]:
    """
    Returns all companies in a peer group with percentile ranks across 10 financial metrics.
    Returns HTTP 404 if peer group is not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check peer group existence
    cursor.execute(
        "SELECT DISTINCT peer_group_name FROM peer_percentiles WHERE LOWER(peer_group_name) = LOWER(?)",
        (group_name.strip(),)
    )
    grp_match = cursor.fetchone()

    if not grp_match:
        # Check raw excel if not in db
        raw_pg_path = PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx"
        found_in_raw = False
        if raw_pg_path.exists():
            import pandas as pd
            try:
                pg_df = pd.read_excel(raw_pg_path)
                m = pg_df[pg_df["peer_group_name"].str.lower() == group_name.strip().lower()]
                if not m.empty:
                    found_in_raw = True
                    canonical_name = m["peer_group_name"].iloc[0]
            except Exception:
                pass

        if not found_in_raw:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found in universe.")
    else:
        canonical_name = grp_match["peer_group_name"]

    query = """
        SELECT pp.*, c.company_name, s.sector, s.industry
        FROM peer_percentiles pp
        JOIN companies c ON pp.company_id = c.company_id
        LEFT JOIN sectors s ON pp.company_id = s.company_id
        WHERE LOWER(pp.peer_group_name) = LOWER(?)
        ORDER BY pp.composite_quality_score_percentile DESC
    """
    cursor.execute(query, (group_name.strip(),))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "peer_group_name": canonical_name,
        "count": len(rows),
        "constituents": rows
    }
