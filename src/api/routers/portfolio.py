"""
Portfolio Statistics Router.
Endpoint: GET /api/v1/portfolio/stats
"""

from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["Portfolio Statistics"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PORTFOLIO_STATS_PATH = PROJECT_ROOT / "output" / "portfolio_stats.csv"


@router.get("/stats", summary="Portfolio Distribution Percentiles (P10–P90)")
def get_portfolio_stats() -> List[Dict[str, Any]]:
    """
    Returns distribution statistics (P10, P25, Median P50, P75, P90, Mean, Standard Deviation)
    across the 92 constituents for 10 core financial metrics.
    """
    if PORTFOLIO_STATS_PATH.exists():
        try:
            df = pd.read_csv(PORTFOLIO_STATS_PATH)
            return df.to_dict("records")
        except Exception:
            pass

    # Dynamic fallback
    from src.analytics.clustering import run_full_clustering_pipeline
    _, _, stats_df = run_full_clustering_pipeline()
    return stats_df.to_dict("records")
