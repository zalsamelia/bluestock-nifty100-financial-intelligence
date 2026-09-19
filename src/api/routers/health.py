"""
Health & System Diagnostic Router.
Endpoint: GET /api/v1/health
"""

import time
import sqlite3
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter(tags=["System Diagnostics"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
START_TIME = time.time()

ALL_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "financial_ratios",
    "peer_percentiles"
]


@router.get("/health", summary="System Health & Database Table Row Counts")
def get_health() -> Dict[str, Any]:
    """
    Returns system status, uptime in seconds, version, and live row counts across all 10 SQLite database tables.
    """
    uptime = round(time.time() - START_TIME, 2)
    row_counts = {}

    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        for tbl in ALL_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                cnt = cursor.fetchone()[0]
                row_counts[tbl] = cnt
            except Exception:
                row_counts[tbl] = 0
        conn.close()
    else:
        for tbl in ALL_TABLES:
            row_counts[tbl] = 0

    return {
        "status": "ok",
        "db_row_counts": row_counts,
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "service": "Bluestock Nifty 100 Financial Intelligence REST Service"
    }
