"""
Valuation & Market Multiples Router.
Endpoint: GET /api/v1/market-cap/{ticker}
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Valuation & Market Cap"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
MCAP_PATH = PROJECT_ROOT / "data" / "raw" / "market_cap.xlsx"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/market-cap/{ticker}", summary="Historical Valuation Multiples & Market Cap (2019–2024)")
def get_company_valuation(ticker: str) -> Dict[str, Any]:
    """
    Returns annual valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield) from 2019 to 2024.
    Returns HTTP 404 if ticker is not found.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id, company_name FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    comp_name = comp["company_name"]
    conn.close()

    # Load market_cap data
    valuation_records = []
    if MCAP_PATH.exists():
        try:
            mdf = pd.read_excel(MCAP_PATH)
            # Find column for company_id
            cid_col = next((c for c in mdf.columns if "company" in str(c).lower() or "ticker" in str(c).lower()), mdf.columns[0])
            c_rows = mdf[mdf[cid_col].astype(str).str.upper() == t_clean]

            for _, row in c_rows.iterrows():
                valuation_records.append({
                    "year": int(row.get("year", 2024)) if pd.notna(row.get("year")) else 2024,
                    "market_cap_cr": round(float(row.get("market_cap", 0)), 2) if pd.notna(row.get("market_cap")) else None,
                    "pe_ratio": round(float(row.get("pe_ratio", 0)), 2) if pd.notna(row.get("pe_ratio")) else None,
                    "pb_ratio": round(float(row.get("pb_ratio", 0)), 2) if pd.notna(row.get("pb_ratio")) else None,
                    "ev_ebitda": round(float(row.get("ev_ebitda", 0)), 2) if pd.notna(row.get("ev_ebitda")) else None,
                    "dividend_yield_pct": round(float(row.get("dividend_yield", 0)), 2) if pd.notna(row.get("dividend_yield")) else None
                })
        except Exception:
            pass

    # If no records in raw excel, fallback to financial_ratios
    if not valuation_records:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM financial_ratios WHERE UPPER(company_id) = ? ORDER BY year ASC", (t_clean,))
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            valuation_records.append({
                "year": r["year"],
                "pe_ratio": r.get("pe_ratio"),
                "pb_ratio": r.get("pb_ratio"),
                "ev_ebitda": r.get("ev_ebitda"),
                "dividend_yield_pct": r.get("dividend_yield_pct")
            })

    return {
        "company_id": t_clean,
        "company_name": comp_name,
        "historical_valuation": valuation_records
    }
