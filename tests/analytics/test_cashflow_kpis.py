"""
Unit Tests for Cash Flow Intelligence Module (Sprint 5 — Days 31 & 32).
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.analytics.cashflow_kpis import (
    classify_cfo_quality, classify_capex_intensity, compute_cagr, generate_cashflow_intelligence
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
CASHFLOW_EXCEL = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_CSV = OUTPUT_DIR / "distress_alerts.csv"
PATTERN_CHANGES_CSV = OUTPUT_DIR / "pattern_changes.csv"


def test_classify_cfo_quality():
    assert classify_cfo_quality(1.5) == "High Quality"
    assert classify_cfo_quality(0.8) == "Moderate"
    assert classify_cfo_quality(0.3) == "Accrual Risk"
    assert classify_cfo_quality(None) == "Moderate"


def test_classify_capex_intensity():
    assert classify_capex_intensity(2.0) == "Asset Light"
    assert classify_capex_intensity(5.5) == "Moderate"
    assert classify_capex_intensity(12.0) == "Capital Intensive"
    assert classify_capex_intensity(None) == "Moderate"


def test_compute_cagr():
    # 100 to 200 over 4 periods = 18.92%
    res = compute_cagr(100.0, 200.0, 4)
    assert res is not None
    assert 18.0 <= res <= 19.5


def test_generate_cashflow_intelligence_outputs():
    """Verify generated Excel and CSV outputs."""
    intel_df, dist_df, pattern_df = generate_cashflow_intelligence()

    assert isinstance(intel_df, pd.DataFrame)
    assert len(intel_df) == 92
    assert CASHFLOW_EXCEL.exists()
    assert DISTRESS_CSV.exists()
    assert PATTERN_CHANGES_CSV.exists()

    required_cols = [
        "company_id", "sector", "cfo_quality_score", "cfo_quality_label",
        "capex_intensity_pct", "capex_label", "fcf_cagr_5yr", "fcf_conversion_pct",
        "distress_flag", "deleveraging_flag", "capital_allocation_label"
    ]
    for col in required_cols:
        assert col in intel_df.columns, f"Missing required column {col}"
