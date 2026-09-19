"""
Regulatory Documents & Annual Reports Router.
Endpoint: GET /api/v1/documents/{ticker}
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/documents", tags=["Regulatory Filings"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/{ticker}", summary="Statutory Annual Reports & BSE Filing Links")
def get_documents_by_ticker(ticker: str) -> List[Dict[str, Any]]:
    """
    Returns all statutory annual report links and document verification flags for a company.
    Returns HTTP 404 if company is not found.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id, company_name FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    cursor.execute("SELECT * FROM documents WHERE UPPER(company_id) = ? ORDER BY year DESC", (t_clean,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        url = r.get("annual_report", "")
        r["is_url_valid"] = bool(url and str(url).strip().startswith("http"))

    return rows
