"""
Unit Tests for CAGR Engine (Day 10).
"""

import pytest
from src.analytics.cagr import calculate_cagr, calculate_series_cagr


def test_cagr_normal():
    """Test normal positive CAGR calculation."""
    # 100 to 161.051 over 5 years is ~10% CAGR
    val, flag = calculate_cagr(start_val=100.0, end_val=161.051, n_years=5)
    assert val == pytest.approx(10.0, abs=1e-3)
    assert flag == "NORMAL"


def test_cagr_turnaround():
    """Test negative to positive turnaround edge case."""
    val, flag = calculate_cagr(start_val=-50.0, end_val=100.0, n_years=5)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss():
    """Test positive to negative decline to loss edge case."""
    val, flag = calculate_cagr(start_val=100.0, end_val=-20.0, n_years=5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_both_negative():
    """Test both negative edge case."""
    val, flag = calculate_cagr(start_val=-100.0, end_val=-50.0, n_years=5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    """Test zero base edge case."""
    val, flag = calculate_cagr(start_val=0.0, end_val=100.0, n_years=5)
    assert val is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_data():
    """Test missing or insufficient data."""
    val, flag = calculate_cagr(start_val=None, end_val=100.0, n_years=5)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_series_cagr_normal_5yr():
    """Test series CAGR for 5-year window with valid historical map."""
    history = {
        2015: 100.0,
        2016: 110.0,
        2017: 120.0,
        2018: 130.0,
        2019: 140.0,
        2020: 161.051
    }
    val, flag = calculate_series_cagr(history, target_year=2020, n_years=5)
    assert val == pytest.approx(10.0, abs=1e-3)
    assert flag == "NORMAL"


def test_series_cagr_missing_start_year():
    """Test series CAGR when target_year - n_years is missing in history."""
    history = {
        2018: 120.0,
        2019: 140.0,
        2020: 160.0
    }
    val, flag = calculate_series_cagr(history, target_year=2020, n_years=5)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_series_cagr_3yr_and_10yr():
    """Test 3-year and 10-year series CAGR windows."""
    history = {
        2010: 100.0,
        2017: 200.0,
        2020: 259.374246
    }
    # 10-year from 2010 to 2020 (100 -> 259.374246 is ~10% CAGR)
    val_10, flag_10 = calculate_series_cagr(history, target_year=2020, n_years=10)
    assert val_10 == pytest.approx(10.0, abs=1e-3)
    assert flag_10 == "NORMAL"

    # 3-year from 2017 to 2020 (200 -> 259.374246 is ~9.05% CAGR)
    val_3, flag_3 = calculate_series_cagr(history, target_year=2020, n_years=3)
    assert val_3 == pytest.approx(9.05, abs=1e-2)
    assert flag_3 == "NORMAL"
