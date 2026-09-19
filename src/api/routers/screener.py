"""
Financial Screener Router.
Endpoint: GET /api/v1/screener
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/screener", tags=["Screener & Ranking"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("", summary="Multi-Metric Fundamental Screener Engine")
def run_screener(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (ROE %)"),
    max_roe: Optional[float] = Query(None, description="Maximum Return on Equity (ROE %)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt-to-Equity Ratio"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (INR Cr)"),
    sector: Optional[str] = Query(None, description="Filter by sector name"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Year Revenue CAGR (%)"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Year Net Profit CAGR (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum Price-to-Earnings (P/E) multiple")
) -> Dict[str, Any]:
    """
    Filters and ranks Nifty 100 companies based on customizable fundamental thresholds.
    Returns HTTP 400 if parameter bounds are mathematically invalid.
    """
    # Validation
    if min_roe is not None and min_roe < -100.0:
        raise HTTPException(status_code=400, detail="Invalid min_roe parameter: value cannot be below -100%.")
    if max_roe is not None and min_roe is not None and min_roe > max_roe:
        raise HTTPException(status_code=400, detail="Invalid range: min_roe cannot be greater than max_roe.")
    if max_de is not None and max_de < 0.0:
        raise HTTPException(status_code=400, detail="Invalid max_de parameter: Debt-to-Equity cannot be negative.")
    if max_pe is not None and max_pe <= 0.0:
        raise HTTPException(status_code=400, detail="Invalid max_pe parameter: P/E multiple must be positive.")

    conn = get_db_connection()
    query = """
        SELECT c.company_id, c.company_name, s.sector, s.industry, s.market_cap_category,
               fr.return_on_equity_pct, fr.debt_to_equity, fr.free_cash_flow_cr,
               fr.revenue_cagr_5yr, fr.pat_cagr_5yr, fr.composite_quality_score
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
             AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.company_id)
        WHERE 1=1
    """
    params = []

    if sector:
        query += " AND LOWER(s.sector) = LOWER(?)"
        params.append(sector)

    if min_roe is not None:
        query += " AND fr.return_on_equity_pct >= ?"
        params.append(min_roe)

    if max_roe is not None:
        query += " AND fr.return_on_equity_pct <= ?"
        params.append(max_roe)

    if max_de is not None:
        query += " AND fr.debt_to_equity <= ?"
        params.append(max_de)

    if min_fcf is not None:
        query += " AND fr.free_cash_flow_cr >= ?"
        params.append(min_fcf)

    if min_rev_cagr_5yr is not None:
        query += " AND fr.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)

    if min_pat_cagr_5yr is not None:
        query += " AND fr.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    # Check valuation table for true P/E if available
    val_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    pe_map = {}
    if val_path.exists():
        try:
            v_df = pd.read_excel(val_path)
            pe_map = dict(zip(v_df["company_id"], v_df["pe_ratio"]))
        except Exception:
            pass

    query += " ORDER BY fr.composite_quality_score DESC, fr.return_on_equity_pct DESC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    raw_results = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Apply P/E map and filter if max_pe specified
    filtered = []
    for r in raw_results:
        cid = r["company_id"]
        pe = pe_map.get(cid, None)
        r["pe_ratio"] = pe

        if max_pe is not None:
            if pe is None or pe > max_pe:
                continue
        filtered.append(r)

    return {
        "status": "success",
        "count": len(filtered),
        "filters_applied": {
            "min_roe": min_roe,
            "max_roe": max_roe,
            "max_de": max_de,
            "min_fcf": min_fcf,
            "sector": sector,
            "min_rev_cagr_5yr": min_rev_cagr_5yr,
            "min_pat_cagr_5yr": min_pat_cagr_5yr,
            "max_pe": max_pe,
        },
        "data": filtered,
    }
