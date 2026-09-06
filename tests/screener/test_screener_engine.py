"""
Unit tests for Financial Screener & Filter Engine (Sprint 3 — Epic 03).
Tests configuration loading, threshold filtering across all 15 metrics,
edge case rules (Financials D/E carve-out, ICR Debt Free infinity),
multi-year YoY D/E declining condition, P10/P90 sector winsorisation,
0-100 composite quality score, and preset screener yields (5-50 companies).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.screener.engine import (
    load_screener_config,
    apply_threshold_filters,
    winsorize_and_scale_metric,
    calculate_composite_quality_score,
    run_screener,
)


def test_load_screener_config():
    """Verify screener_config.yaml loads with all required presets and weights."""
    config = load_screener_config()
    assert "presets" in config
    assert "composite_score_weights" in config
    assert "metric_mappings" in config

    expected_presets = [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ]
    for p in expected_presets:
        assert p in config["presets"]
        assert "filters" in config["presets"][p]


def test_apply_threshold_filters_basic():
    """Test basic threshold filtering on numeric metrics."""
    df = pd.DataFrame([
        {"company_id": "C1", "sector": "Technology", "return_on_equity_pct": 20.0, "debt_to_equity": 0.2, "free_cash_flow_cr": 500.0},
        {"company_id": "C2", "sector": "Technology", "return_on_equity_pct": 10.0, "debt_to_equity": 0.5, "free_cash_flow_cr": 100.0},
        {"company_id": "C3", "sector": "Automobile", "return_on_equity_pct": 25.0, "debt_to_equity": 1.5, "free_cash_flow_cr": -50.0},
    ])

    filters = {"return_on_equity_pct_min": 15.0, "debt_to_equity_max": 1.0, "free_cash_flow_cr_min": 0.0}
    res = apply_threshold_filters(df, filters)
    assert len(res) == 1
    assert res.iloc[0]["company_id"] == "C1"


def test_financials_sector_de_carveout():
    """Verify Financials sector companies bypass the D/E max filter."""
    df = pd.DataFrame([
        {"company_id": "BANK1", "sector": "Financials", "debt_to_equity": 6.5, "return_on_equity_pct": 16.0},
        {"company_id": "MFG1", "sector": "Manufacturing", "debt_to_equity": 6.5, "return_on_equity_pct": 16.0},
        {"company_id": "MFG2", "sector": "Manufacturing", "debt_to_equity": 0.5, "return_on_equity_pct": 16.0},
    ])

    filters = {"debt_to_equity_max": 1.0}
    
    # With carve-out (default): BANK1 and MFG2 should pass, MFG1 should fail
    res_carveout = apply_threshold_filters(df, filters, is_financials_carveout=True)
    assert set(res_carveout["company_id"]) == {"BANK1", "MFG2"}

    # Without carve-out: only MFG2 passes
    res_no_carveout = apply_threshold_filters(df, filters, is_financials_carveout=False)
    assert set(res_no_carveout["company_id"]) == {"MFG2"}


def test_icr_debt_free_infinity_handling():
    """Verify debt-free companies pass ICR minimum filters automatically, while non-debt-free nulls fail."""
    df = pd.DataFrame([
        {"company_id": "DF1", "interest_coverage": None, "icr_label": "Debt Free", "debt_to_equity": 0.0},
        {"company_id": "DIRTY_NON_DEBT_FREE", "interest_coverage": np.nan, "icr_label": "Normal", "debt_to_equity": 2.5},
        {"company_id": "LEVERAGED_PASS", "interest_coverage": 10.0, "icr_label": "Normal", "debt_to_equity": 1.2},
        {"company_id": "LEVERAGED_FAIL", "interest_coverage": 1.5, "icr_label": "Normal", "debt_to_equity": 1.5},
    ])

    filters = {"interest_coverage_min": 3.0}
    res = apply_threshold_filters(df, filters)
    passed_ids = set(res["company_id"])
    assert "DF1" in passed_ids
    assert "LEVERAGED_PASS" in passed_ids
    assert "DIRTY_NON_DEBT_FREE" not in passed_ids
    assert "LEVERAGED_FAIL" not in passed_ids


def test_turnaround_watch_yoy_de_declining():
    """Verify multi-year D/E declining YoY filter logic."""
    df = pd.DataFrame([
        {"company_id": "IMPROVING", "revenue_cagr_3yr": 12.0, "free_cash_flow_cr": 100.0, "debt_to_equity": 0.8, "debt_to_equity_prev": 1.2},
        {"company_id": "WORSENING", "revenue_cagr_3yr": 15.0, "free_cash_flow_cr": 200.0, "debt_to_equity": 1.5, "debt_to_equity_prev": 1.0},
        {"company_id": "DEBT_FREE", "revenue_cagr_3yr": 14.0, "free_cash_flow_cr": 300.0, "debt_to_equity": 0.0, "debt_to_equity_prev": 0.0},
    ])

    filters = {
        "revenue_cagr_3yr_min": 10.0,
        "free_cash_flow_cr_min": 0.0,
        "de_declining_yoy": True,
    }
    res = apply_threshold_filters(df, filters)
    passed_ids = set(res["company_id"])
    assert "IMPROVING" in passed_ids
    assert "DEBT_FREE" in passed_ids
    assert "WORSENING" not in passed_ids


def test_winsorize_and_scale_metric():
    """Test P10/P90 capping and 0-100 min-max scaling, including inversion."""
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
    
    # Standard ascending scaling (higher is better)
    scaled = winsorize_and_scale_metric(series)
    assert scaled.min() >= 0.0
    assert scaled.max() <= 100.0
    assert scaled.iloc[0] == 0.0
    assert scaled.iloc[-1] == 100.0

    # Inverted scaling (lower is better, e.g. D/E)
    scaled_inv = winsorize_and_scale_metric(series, invert=True)
    assert scaled_inv.iloc[0] == 100.0
    assert scaled_inv.iloc[-1] == 0.0


def test_calculate_composite_quality_score():
    """Verify composite quality score produces values in 0-100 range."""
    df = pd.DataFrame([
        {
            "company_id": "TCS", "sector": "Technology",
            "return_on_equity_pct": 50.0, "roce_pct": 60.0, "net_profit_margin_pct": 20.0,
            "fcf_cagr_5yr": 15.0, "cfo_quality_score": 1.1, "fcf_positive_flag": 1,
            "revenue_cagr_5yr": 12.0, "pat_cagr_5yr": 10.0,
            "debt_to_equity": 0.08, "interest_coverage": 50.0,
        },
        {
            "company_id": "WEAK", "sector": "Technology",
            "return_on_equity_pct": 5.0, "roce_pct": 4.0, "net_profit_margin_pct": 2.0,
            "fcf_cagr_5yr": -10.0, "cfo_quality_score": 0.3, "fcf_positive_flag": 0,
            "revenue_cagr_5yr": 2.0, "pat_cagr_5yr": -5.0,
            "debt_to_equity": 3.0, "interest_coverage": 1.2,
        },
    ])

    scored = calculate_composite_quality_score(df)
    assert "composite_quality_score" in scored.columns
    tcs_score = scored[scored["company_id"] == "TCS"]["composite_quality_score"].iloc[0]
    weak_score = scored[scored["company_id"] == "WEAK"]["composite_quality_score"].iloc[0]
    
    assert 0.0 <= tcs_score <= 100.0
    assert 0.0 <= weak_score <= 100.0
    assert tcs_score > weak_score


def test_all_6_presets_yield_constraint():
    """
    Verify all 6 preset screeners yield between 5 and 50 companies
    on the actual 92-company Nifty 100 universe.
    """
    config = load_screener_config()
    presets = list(config["presets"].keys())
    assert len(presets) == 6

    for preset_key in presets:
        preset_name = config["presets"][preset_key]["name"]
        res_df = run_screener(preset_name=preset_key)
        count = len(res_df)
        assert 5 <= count <= 50, (
            f"Preset '{preset_name}' returned {count} companies, outside expected 5-50 range."
        )
