"""
Financial Screener & Filter Engine (Sprint 3 — Day 15 & Day 17).
Supports 15 filterable metrics, custom threshold filters via screener_config.yaml,
6 preset templates, edge case handling (Financials D/E carve-out, ICR infinity for Debt Free),
P10/P90 sector-relative winsorisation, and 0-100 composite quality score calculation.
"""

import os
import sys
import sqlite3
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.cagr import calculate_series_cagr

DB_PATH = PROJECT_ROOT / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "raw" / "market_cap.xlsx"


def load_screener_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Load and parse the screener YAML configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Screener config not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_full_screener_dataset(db_path: Path = DB_PATH, target_year: int = 2024) -> pd.DataFrame:
    """
    Load and assemble complete dataset for screener calculations:
    - Target year financial_ratios, companies, sectors, profitandloss, balancesheet
    - Valuation metrics from data/raw/market_cap.xlsx
    - Dynamic 5-year FCF CAGR derived from free_cash_flow_cr time series
    - Previous year D/E ratio for YoY trend evaluation
    """
    conn = sqlite3.connect(str(db_path))
    
    # Load all ratios and financial tables
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    pnl_df = pd.read_sql_query("SELECT company_id, year, sales, net_profit FROM profitandloss", conn)
    companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    sectors_df = pd.read_sql_query("SELECT company_id, sector, industry, market_cap_category FROM sectors", conn)
    conn.close()

    # Load market_cap.xlsx for valuation metrics
    if MARKET_CAP_PATH.exists():
        mcap_df = pd.read_excel(MARKET_CAP_PATH)
    else:
        # Fallback empty dataframe if missing
        mcap_df = pd.DataFrame(columns=[
            "company_id", "year", "market_cap_crore", "enterprise_value_crore",
            "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"
        ])

    # Merge financial_ratios with P&L sales/net_profit
    full_ratios = ratios_df.merge(pnl_df, on=["company_id", "year"], how="left")

    # Merge with market_cap.xlsx valuation metrics
    full_ratios = full_ratios.merge(
        mcap_df[["company_id", "year", "market_cap_crore", "pe_ratio", "pb_ratio", "dividend_yield_pct"]],
        on=["company_id", "year"],
        how="left"
    )

    # Compute FCF 5-year CAGR per company dynamically
    fcf_cagr_map = {}
    de_prev_map = {}

    for cid, c_df in full_ratios.groupby("company_id"):
        c_df = c_df.sort_values("year")
        
        # FCF series dict {year: fcf}
        fcf_series = {int(y): float(v) for y, v in zip(c_df["year"], c_df["free_cash_flow_cr"]) if pd.notna(v)}
        val, _ = calculate_series_cagr(fcf_series, target_year, 5)
        fcf_cagr_map[cid] = val

        # D/E previous year lookup
        de_curr = c_df[c_df["year"] == target_year]["debt_to_equity"].values
        de_prev = c_df[c_df["year"] == (target_year - 1)]["debt_to_equity"].values
        if len(de_prev) > 0 and pd.notna(de_prev[0]):
            de_prev_map[cid] = float(de_prev[0])
        else:
            de_prev_map[cid] = None

    # Filter to target_year
    target_df = full_ratios[full_ratios["year"] == target_year].copy()
    if target_df.empty:
        # Fallback to max available year if target_year not found
        max_yr = full_ratios["year"].max()
        target_df = full_ratios[full_ratios["year"] == max_yr].copy()

    # Add metadata
    target_df = target_df.merge(companies_df, on="company_id", how="left")
    target_df = target_df.merge(sectors_df, on="company_id", how="left")

    # Add derived FCF CAGR and previous year D/E
    target_df["fcf_cagr_5yr"] = target_df["company_id"].map(fcf_cagr_map)
    target_df["debt_to_equity_prev"] = target_df["company_id"].map(de_prev_map)

    # FCF positive flag
    target_df["fcf_positive_flag"] = (target_df["free_cash_flow_cr"] > 0).astype(int)

    return target_df


def apply_threshold_filters(
    df: pd.DataFrame,
    filters: Dict[str, Any],
    is_financials_carveout: bool = True
) -> pd.DataFrame:
    """
    Apply metric threshold filters to DataFrame.
    Supports all 15 filterable metrics with edge case handling:
    - Carve-out: Skip debt_to_equity max filter for Financials sector companies if enabled.
    - ICR Debt Free: Always pass ICR minimum filter if company has icr_label == 'Debt Free' or interest_coverage IS NULL.
    """
    filtered = df.copy()

    for rule_key, threshold in filters.items():
        if threshold is None:
            continue

        # 1. Return on Equity (min)
        if rule_key in ["return_on_equity_pct_min", "roe_min"]:
            filtered = filtered[filtered["return_on_equity_pct"] >= threshold]

        # 2. Debt to Equity (max) with Financials sector carve-out
        elif rule_key in ["debt_to_equity_max", "de_max"]:
            if is_financials_carveout and "sector" in filtered.columns:
                # Financials sector passes automatically; non-financials must meet D/E <= threshold
                is_fin = filtered["sector"] == "Financials"
                de_pass = filtered["debt_to_equity"] <= threshold
                filtered = filtered[is_fin | de_pass]
            else:
                filtered = filtered[filtered["debt_to_equity"] <= threshold]

        # 3. Free Cash Flow (min)
        elif rule_key in ["free_cash_flow_cr_min", "fcf_min"]:
            filtered = filtered[filtered["free_cash_flow_cr"] >= threshold]

        # 4. Revenue CAGR 5-year (min)
        elif rule_key in ["revenue_cagr_5yr_min", "rev_cagr_5yr_min"]:
            filtered = filtered[filtered["revenue_cagr_5yr"] >= threshold]

        # 5. PAT CAGR 5-year (min)
        elif rule_key in ["pat_cagr_5yr_min", "pat_cagr_5yr_min"]:
            filtered = filtered[filtered["pat_cagr_5yr"] >= threshold]

        # 6. OPM (min)
        elif rule_key in ["operating_profit_margin_pct_min", "opm_min"]:
            filtered = filtered[filtered["operating_profit_margin_pct"] >= threshold]

        # 7. Price to Earnings P/E (max)
        elif rule_key in ["pe_ratio_max", "pe_max"]:
            filtered = filtered[(filtered["pe_ratio"].notnull()) & (filtered["pe_ratio"] > 0) & (filtered["pe_ratio"] <= threshold)]

        # 8. Price to Book P/B (max)
        elif rule_key in ["pb_ratio_max", "pb_max"]:
            filtered = filtered[(filtered["pb_ratio"].notnull()) & (filtered["pb_ratio"] > 0) & (filtered["pb_ratio"] <= threshold)]

        # 9. Dividend Yield (min)
        elif rule_key in ["dividend_yield_pct_min", "dividend_yield_min"]:
            filtered = filtered[filtered["dividend_yield_pct"] >= threshold]

        # 10. Dividend Payout Ratio (max)
        elif rule_key in ["dividend_payout_ratio_pct_max", "payout_max"]:
            filtered = filtered[filtered["dividend_payout_ratio_pct"] <= threshold]

        # 11. Interest Coverage Ratio (min) with Debt Free infinity handling
        elif rule_key in ["interest_coverage_min", "icr_min"]:
            # Debt Free companies (icr_label == 'Debt Free' or debt_to_equity == 0) strictly pass ICR min as infinity
            has_label = (filtered["icr_label"] == "Debt Free") if "icr_label" in filtered.columns else pd.Series(False, index=filtered.index)
            has_zero_de = (filtered["debt_to_equity"] == 0) if "debt_to_equity" in filtered.columns else pd.Series(False, index=filtered.index)
            is_debt_free = has_label | has_zero_de

            icr_pass = (filtered["interest_coverage"].notnull()) & (filtered["interest_coverage"] >= threshold) if "interest_coverage" in filtered.columns else pd.Series(False, index=filtered.index)
            filtered = filtered[is_debt_free | icr_pass]

        # 12. Market Cap (min)
        elif rule_key in ["market_cap_crore_min", "market_cap_min"]:
            filtered = filtered[filtered["market_cap_crore"] >= threshold]

        # 13. Net Profit (min)
        elif rule_key in ["net_profit_min", "pat_min"]:
            filtered = filtered[filtered["net_profit"] >= threshold]

        # 14. EPS CAGR 5-year (min)
        elif rule_key in ["eps_cagr_5yr_min", "eps_cagr_min"]:
            filtered = filtered[filtered["eps_cagr_5yr"] >= threshold]

        # 15. Asset Turnover (min)
        elif rule_key in ["asset_turnover_min"]:
            filtered = filtered[filtered["asset_turnover"] >= threshold]

        # 16. Sales / Revenue (min)
        elif rule_key in ["sales_min", "revenue_min"]:
            filtered = filtered[filtered["sales"] >= threshold]

        # 17. Revenue CAGR 3-year (min)
        elif rule_key in ["revenue_cagr_3yr_min"]:
            filtered = filtered[filtered["revenue_cagr_3yr"] >= threshold]

        # 18. Multi-year D/E declining YoY
        elif rule_key == "de_declining_yoy" and threshold is True:
            # Check debt_to_equity < debt_to_equity_prev or D/E is 0 / debt-free
            is_df = filtered["debt_to_equity"] == 0
            is_declining = (filtered["debt_to_equity"].notnull()) & (filtered["debt_to_equity_prev"].notnull()) & (filtered["debt_to_equity"] < filtered["debt_to_equity_prev"])
            filtered = filtered[is_df | is_declining]

    return filtered


def winsorize_and_scale_metric(
    series: pd.Series,
    p10: Optional[float] = None,
    p90: Optional[float] = None,
    invert: bool = False
) -> pd.Series:
    """
    Winsorise a metric series at P10/P90 bounds and MinMax scale to 0-100.
    If invert=True (e.g. for D/E), lower raw metric yields higher score (100 - score).
    """
    valid = series.dropna()
    if valid.empty:
        return pd.Series(50.0, index=series.index)

    if p10 is None:
        p10 = float(np.percentile(valid, 10))
    if p90 is None:
        p90 = float(np.percentile(valid, 90))

    # Equal bounds fallback
    if p10 == p90:
        return pd.Series(50.0, index=series.index)

    # Winsorise (cap extreme values)
    capped = series.clip(lower=p10, upper=p90)

    # Scale to 0-100
    scaled = (capped - p10) / (p90 - p10) * 100.0

    if invert:
        scaled = 100.0 - scaled

    # Fill missing values with median score 50.0
    return scaled.fillna(50.0)


def calculate_composite_quality_score(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Compute Composite Quality Score (0 to 100 scale):
    - 35% Profitability: ROE (15%), ROCE (10%), NPM (10%)
    - 30% Cash Quality: FCF CAGR (15%), CFO/PAT ratio (10%), FCF positive flag (5%)
    - 20% Growth: Revenue CAGR 5yr (10%), PAT CAGR 5yr (10%)
    - 15% Leverage: D/E score (10%, inverted), ICR score (5%)

    Winsorises metrics at P10/P90 within broad_sector (or overall universe if sector size < 5).
    """
    res_df = df.copy()
    if res_df.empty:
        res_df["composite_quality_score"] = []
        return res_df

    # Prepare component score columns
    scored_cols = {}
    
    # Check if sector column available
    has_sector = "sector" in res_df.columns

    # Group by sector if sector size >= 5, else global
    if has_sector:
        sector_counts = res_df["sector"].value_counts()
    else:
        sector_counts = {}

    def get_winsorised_score(col_name: str, invert: bool = False) -> pd.Series:
        if col_name not in res_df.columns:
            return pd.Series(50.0, index=res_df.index)
        
        scores = pd.Series(index=res_df.index, dtype=float)
        if has_sector:
            for s_name, s_group in res_df.groupby("sector"):
                if len(s_group) >= 5:
                    scores.loc[s_group.index] = winsorize_and_scale_metric(s_group[col_name], invert=invert)
                else:
                    # Global P10/P90 fallback for small sectors
                    scores.loc[s_group.index] = winsorize_and_scale_metric(res_df[col_name], invert=invert).loc[s_group.index]
        else:
            scores = winsorize_and_scale_metric(res_df[col_name], invert=invert)
        return scores

    # Compute individual metric scores (0-100)
    score_roe = get_winsorised_score("return_on_equity_pct")
    score_roce = get_winsorised_score("roce_pct")
    score_npm = get_winsorised_score("net_profit_margin_pct")

    score_fcf_cagr = get_winsorised_score("fcf_cagr_5yr")
    score_cfo_quality = get_winsorised_score("cfo_quality_score")
    score_fcf_pos = res_df["fcf_positive_flag"].fillna(0) * 100.0 if "fcf_positive_flag" in res_df.columns else pd.Series(50.0, index=res_df.index)

    score_rev_cagr = get_winsorised_score("revenue_cagr_5yr")
    score_pat_cagr = get_winsorised_score("pat_cagr_5yr")

    score_de = get_winsorised_score("debt_to_equity", invert=True)
    score_icr = get_winsorised_score("interest_coverage")

    # Weighted Composite Quality Score
    composite = (
        0.15 * score_roe +
        0.10 * score_roce +
        0.10 * score_npm +
        0.15 * score_fcf_cagr +
        0.10 * score_cfo_quality +
        0.05 * score_fcf_pos +
        0.10 * score_rev_cagr +
        0.10 * score_pat_cagr +
        0.10 * score_de +
        0.05 * score_icr
    )

    res_df["composite_quality_score"] = composite.round(2)
    return res_df


def run_screener(
    preset_name: Optional[str] = None,
    custom_filters: Optional[Dict[str, Any]] = None,
    target_year: int = 2024,
    config_path: Path = CONFIG_PATH
) -> pd.DataFrame:
    """
    Run screener query with specified preset template or custom threshold filters.
    Returns filtered and sorted DataFrame by composite_quality_score descending.
    """
    config = load_screener_config(config_path)
    df = load_full_screener_dataset(target_year=target_year)

    filters_to_apply = {}

    if preset_name:
        presets = config.get("presets", {})
        if preset_name not in presets:
            raise ValueError(f"Unknown preset template '{preset_name}'. Available: {list(presets.keys())}")
        filters_to_apply = presets[preset_name].get("filters", {})
    elif custom_filters:
        filters_to_apply = custom_filters

    # Apply threshold filters
    filtered_df = apply_threshold_filters(df, filters_to_apply)

    # Compute composite quality score
    scored_df = calculate_composite_quality_score(filtered_df, config)

    # Sort by composite_quality_score descending
    sorted_df = scored_df.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)

    return sorted_df
