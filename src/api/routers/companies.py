"""
Companies Router.
Endpoints:
- GET /api/v1/companies
- GET /api/v1/companies/{ticker}
- GET /api/v1/companies/{ticker}/pl
- GET /api/v1/companies/{ticker}/bs
- GET /api/v1/companies/{ticker}/cashflow
- GET /api/v1/companies/{ticker}/ratios
- GET /api/v1/companies/{ticker}/tearsheet
- GET /api/v1/companies/{ticker}/peers/compare
- GET /api/v1/companies/{ticker}/documents
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse

router = APIRouter(prefix="/companies", tags=["Companies & Fundamentals"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def parse_year_param(val: Optional[str]) -> Optional[int]:
    """Parse year from YYYY-MM or YYYY string."""
    if not val:
        return None
    try:
        val_str = str(val).strip()
        if "-" in val_str:
            return int(val_str.split("-")[0])
        return int(val_str)
    except Exception:
        return None


@router.get("", summary="List All Constituents with Basic Return Metrics")
def list_companies(
    sector: Optional[str] = Query(None, description="Filter by broad sector name"),
    market_cap_category: Optional[str] = Query(None, description="Filter by Large Cap / Mid Cap"),
    search: Optional[str] = Query(None, description="Partial search query on ticker or company name")
) -> List[Dict[str, Any]]:
    """
    Returns list of companies with id, company_name, broad_sector, sub_sector, roe_pct, roce_pct.
    """
    conn = get_db_connection()
    query = """
        SELECT c.company_id AS id, c.company_name, 
               s.sector AS broad_sector, s.industry AS sub_sector,
               s.market_cap_category,
               fr.return_on_equity_pct AS roe_pct,
               fr.roce_pct AS roce_pct
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

    if market_cap_category:
        query += " AND LOWER(s.market_cap_category) = LOWER(?)"
        params.append(market_cap_category)

    if search:
        query += " AND (LOWER(c.company_id) LIKE LOWER(?) OR LOWER(c.company_name) LIKE LOWER(?))"
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    query += " ORDER BY c.company_id ASC"

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/{ticker}", summary="Detailed Company Profile & Latest Financials")
def get_company_profile(ticker: str) -> Dict[str, Any]:
    """
    Returns comprehensive profile: metadata, sector classifications, and latest year ratios.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    comp_row = cursor.fetchone()
    if not comp_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    comp_dict = dict(comp_row)

    cursor.execute("SELECT * FROM sectors WHERE UPPER(company_id) = ?", (t_clean,))
    sec_row = cursor.fetchone()
    if sec_row:
        comp_dict["sector_info"] = dict(sec_row)

    cursor.execute(
        "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ? ORDER BY year DESC LIMIT 1",
        (t_clean,)
    )
    ratio_row = cursor.fetchone()
    if ratio_row:
        comp_dict["latest_ratios"] = dict(ratio_row)

    conn.close()
    return comp_dict


@router.get("/{ticker}/pl", summary="Historical Profit & Loss Statements")
def get_company_pl(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)")
) -> List[Dict[str, Any]]:
    """
    Returns annual Profit & Loss statement history.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check existence
    cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    query = "SELECT * FROM profitandloss WHERE UPPER(company_id) = ?"
    params = [t_clean]

    start_y = parse_year_param(from_year)
    if start_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) >= ?"
        params.append(start_y)

    end_y = parse_year_param(to_year)
    if end_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?"
        params.append(end_y)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/{ticker}/bs", summary="Historical Balance Sheet Statements")
def get_company_bs(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)")
) -> List[Dict[str, Any]]:
    """
    Returns annual Balance Sheet history.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    query = "SELECT * FROM balancesheet WHERE UPPER(company_id) = ?"
    params = [t_clean]

    start_y = parse_year_param(from_year)
    if start_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) >= ?"
        params.append(start_y)

    end_y = parse_year_param(to_year)
    if end_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?"
        params.append(end_y)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/{ticker}/cashflow", summary="Historical Cash Flow Statements")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)")
) -> List[Dict[str, Any]]:
    """
    Returns annual Cash Flow statement history.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    query = "SELECT * FROM cashflow WHERE UPPER(company_id) = ?"
    params = [t_clean]

    start_y = parse_year_param(from_year)
    if start_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) >= ?"
        params.append(start_y)

    end_y = parse_year_param(to_year)
    if end_y:
        query += " AND CAST(SUBSTR(year, 1, 4) AS INTEGER) <= ?"
        params.append(end_y)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/{ticker}/ratios", summary="Computed Financial Ratios & Performance Indicators")
def get_company_ratios(
    ticker: str,
    year: Optional[int] = Query(None, description="Optional specific fiscal year (e.g. 2024)")
) -> List[Dict[str, Any]]:
    """
    Returns computed ratios (ROE, ROCE, Margins, Leverage, Quality Score).
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    query = "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ?"
    params = [t_clean]

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/{ticker}/tearsheet", summary="Download Institutional 2-Page PDF Tearsheet")
def download_tearsheet(ticker: str):
    """
    Streams the pre-generated ReportLab 2-page tearsheet PDF for direct binary download.
    """
    t_clean = ticker.upper().strip()
    pdf_path = TEARSHEET_DIR / f"{t_clean}_tearsheet.pdf"

    if not pdf_path.exists():
        # Check if company exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
        exists = cursor.fetchone()
        conn.close()

        if not exists:
            raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

        # Attempt to dynamically generate if missing
        try:
            from src.reports.tearsheet import generate_company_tearsheet
            res = generate_company_tearsheet(t_clean)
            if not res or not Path(res).exists():
                raise HTTPException(status_code=404, detail=f"Tearsheet PDF not available for '{ticker}'.")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Tearsheet PDF could not be generated: {e}")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{t_clean}_tearsheet.pdf"
    )


@router.get("/{ticker}/peers/compare", summary="8-Axis Radar Chart Comparison Data")
def get_peer_radar_compare(ticker: str) -> Dict[str, Any]:
    """
    Returns 8-axis metric comparison for company vs its peer group average.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    # Find peer group from peer_percentiles
    cursor.execute(
        "SELECT peer_group_name FROM peer_percentiles WHERE UPPER(company_id) = ? LIMIT 1",
        (t_clean,)
    )
    peer_row = cursor.fetchone()
    peer_group = peer_row["peer_group_name"] if peer_row else None

    # Fetch latest ratios for target company
    cursor.execute(
        "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ? ORDER BY year DESC LIMIT 1",
        (t_clean,)
    )
    comp_ratio = dict(cursor.fetchone() or {})

    metrics = [
        "return_on_equity_pct", "roce_pct", "net_profit_margin_pct",
        "operating_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr",
        "pat_cagr_5yr", "composite_quality_score"
    ]

    company_vals = {m: comp_ratio.get(m, 0.0) or 0.0 for m in metrics}

    peer_avg = {}
    if peer_group:
        # Get all companies in the same peer group
        cursor.execute(
            "SELECT DISTINCT company_id FROM peer_percentiles WHERE peer_group_name = ? AND UPPER(company_id) != ?",
            (peer_group, t_clean)
        )
        peer_companies = [r["company_id"] for r in cursor.fetchall()]

        for m in metrics:
            vals = []
            for cid in peer_companies:
                cursor.execute(
                    "SELECT value FROM peer_percentiles WHERE company_id = ? AND metric = ? ORDER BY year DESC LIMIT 1",
                    (cid, m)
                )
                row = cursor.fetchone()
                if row and row["value"] is not None:
                    vals.append(float(row["value"]))
            peer_avg[m] = round(float(sum(vals) / len(vals)), 2) if vals else 0.0
    else:
        peer_avg = {m: 0.0 for m in metrics}

    conn.close()

    return {
        "target_company": t_clean,
        "company_name": comp["company_name"],
        "peer_group": peer_group or "Unknown",
        "axis_metrics": metrics,
        "company_values": company_vals,
        "peer_group_average": peer_avg,
    }


@router.get("/{ticker}/documents", summary="Filing Disclosures with URL Validation")
def get_company_documents(ticker: str) -> List[Dict[str, Any]]:
    """
    Returns annual reports and filings with an is_url_valid boolean flag.
    """
    t_clean = ticker.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT company_id FROM companies WHERE UPPER(company_id) = ?", (t_clean,))
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
