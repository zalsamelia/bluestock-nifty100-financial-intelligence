"""
Composite Financial Quality Score Analytics Module.
Computes a weighted 0-100 composite score based on ROE, FCF, ROCE, and D/E ratios.
Formula:
0.30 * ROE_score + 0.25 * FCF_score + 0.25 * ROCE_score + 0.20 * DE_score
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_percentile_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes percentile-ranked sub-scores (0-100) for key metrics across company-years.
    Handles missing values gracefully.
    """
    df_scored = df.copy()

    # ROE score (higher is better)
    if "return_on_equity_pct" in df_scored.columns and df_scored["return_on_equity_pct"].notnull().any():
        df_scored["roe_score"] = df_scored["return_on_equity_pct"].rank(pct=True, ascending=True) * 100.0
    else:
        df_scored["roe_score"] = 50.0

    # FCF score (higher is better)
    if "free_cash_flow_cr" in df_scored.columns and df_scored["free_cash_flow_cr"].notnull().any():
        df_scored["fcf_score"] = df_scored["free_cash_flow_cr"].rank(pct=True, ascending=True) * 100.0
    else:
        df_scored["fcf_score"] = 50.0

    # ROCE score (higher is better)
    if "roce_pct" in df_scored.columns and df_scored["roce_pct"].notnull().any():
        df_scored["roce_score"] = df_scored["roce_pct"].rank(pct=True, ascending=True) * 100.0
    else:
        df_scored["roce_score"] = 50.0

    # D/E score (lower is better, so ascending=False)
    if "debt_to_equity" in df_scored.columns and df_scored["debt_to_equity"].notnull().any():
        df_scored["de_score"] = df_scored["debt_to_equity"].rank(pct=True, ascending=False) * 100.0
    else:
        df_scored["de_score"] = 50.0

    # Fill NaNs with median score (50.0)
    df_scored["roe_score"] = df_scored["roe_score"].fillna(50.0)
    df_scored["fcf_score"] = df_scored["fcf_score"].fillna(50.0)
    df_scored["roce_score"] = df_scored["roce_score"].fillna(50.0)
    df_scored["de_score"] = df_scored["de_score"].fillna(50.0)

    # Composite Score calculation
    df_scored["composite_quality_score"] = (
        0.30 * df_scored["roe_score"] +
        0.25 * df_scored["fcf_score"] +
        0.25 * df_scored["roce_score"] +
        0.20 * df_scored["de_score"]
    ).round(2)

    return df_scored
