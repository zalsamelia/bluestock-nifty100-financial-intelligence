"""
Unit tests for Valuation Analytics Module (Sprint 4 — Day 26 & Day 27).
Tests FCF yield calculation, sector median P/E, valuation flag classification (Caution, Discount, Fair),
and report generation (valuation_summary.xlsx & valuation_flags.csv).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.analytics.valuation import (
    compute_fcf_yield,
    classify_valuation_flag,
    run_valuation_analysis,
    generate_valuation_reports,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def test_compute_fcf_yield_normal():
    """Test FCF yield computation under normal positive conditions."""
    fcf = 1500.0  # ₹ Cr
    mcap = 30000.0  # ₹ Cr
    yield_val = compute_fcf_yield(fcf, mcap)
    assert yield_val == pytest.approx(5.0, 0.01)


def test_compute_fcf_yield_edge_cases():
    """Test FCF yield edge cases: negative FCF, zero/negative market cap, None inputs."""
    # Negative FCF
    assert compute_fcf_yield(-500.0, 10000.0) == pytest.approx(-5.0, 0.01)
    
    # Zero or negative market cap
    assert compute_fcf_yield(500.0, 0.0) is None
    assert compute_fcf_yield(500.0, -100.0) is None
    
    # None inputs
    assert compute_fcf_yield(None, 10000.0) is None
    assert compute_fcf_yield(500.0, None) is None


def test_classify_valuation_flag():
    """Test overvaluation and discount flag classification logic."""
    sector_median = 30.0

    # Caution: P/E > 1.5 * 30.0 = 45.0
    assert classify_valuation_flag(50.0, sector_median) == "Caution"
    assert classify_valuation_flag(60.0, sector_median) == "Caution"

    # Discount: P/E < 0.7 * 30.0 = 21.0
    assert classify_valuation_flag(18.0, sector_median) == "Discount"
    assert classify_valuation_flag(15.0, sector_median) == "Discount"

    # Fair: Between 21.0 and 45.0
    assert classify_valuation_flag(30.0, sector_median) == "Fair"
    assert classify_valuation_flag(25.0, sector_median) == "Fair"
    assert classify_valuation_flag(40.0, sector_median) == "Fair"

    # Null / Missing
    assert classify_valuation_flag(None, sector_median) == "Fair"
    assert classify_valuation_flag(30.0, None) == "Fair"


def test_run_valuation_analysis_full_universe():
    """Verify run_valuation_analysis covers all 92 companies with required columns."""
    df = run_valuation_analysis(target_year=2024)
    assert len(df) == 92
    assert "company_id" in df.columns
    assert "fcf_yield_pct" in df.columns
    assert "sector_median_pe" in df.columns
    assert "pe_vs_sector_median_pct" in df.columns
    assert "valuation_flag" in df.columns

    # Verify all flags belong to valid set
    valid_flags = {"Caution", "Discount", "Fair"}
    assert set(df["valuation_flag"].unique()).issubset(valid_flags)


def test_generate_valuation_reports():
    """Verify generation of valuation_summary.xlsx and valuation_flags.csv."""
    xlsx_path, csv_path = generate_valuation_reports(OUTPUT_DIR)

    assert xlsx_path.exists()
    assert csv_path.exists()

    # Verify CSV content
    flags_df = pd.read_csv(csv_path)
    assert not flags_df.empty
    assert set(flags_df["valuation_flag"].unique()).issubset({"Caution", "Discount"})
