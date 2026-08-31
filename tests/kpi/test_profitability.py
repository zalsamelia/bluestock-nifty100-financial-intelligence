"""
Unit Tests for Profitability Ratios (Day 08).
"""

import pytest
from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_opm,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_book_value_per_share,
)


def test_npm_normal():
    """Test NPM calculation under normal conditions."""
    npm = calculate_net_profit_margin(net_profit=150.0, sales=1000.0)
    assert npm == pytest.approx(15.0)


def test_npm_zero_sales():
    """Test NPM calculation when sales is zero (should return None)."""
    npm = calculate_net_profit_margin(net_profit=150.0, sales=0.0)
    assert npm is None


def test_opm_normal():
    """Test OPM calculation under normal conditions."""
    opm, mismatch = calculate_opm(operating_profit=200.0, sales=1000.0, source_opm=20.0)
    assert opm == pytest.approx(20.0)
    assert mismatch is None


def test_opm_crosscheck_mismatch():
    """Test OPM calculation with >1% mismatch vs source OPM."""
    opm, mismatch = calculate_opm(operating_profit=200.0, sales=1000.0, source_opm=15.0)
    assert opm == pytest.approx(20.0)
    assert mismatch is not None
    assert mismatch["difference"] == pytest.approx(5.0)


def test_roe_normal():
    """Test ROE calculation under normal positive equity conditions."""
    roe = calculate_roe(net_profit=100.0, equity_capital=20.0, reserves=480.0)
    assert roe == pytest.approx(20.0)


def test_roe_negative_or_zero_equity():
    """Test ROE calculation when equity + reserves <= 0 (should return None)."""
    roe_zero = calculate_roe(net_profit=100.0, equity_capital=10.0, reserves=-10.0)
    roe_neg = calculate_roe(net_profit=100.0, equity_capital=10.0, reserves=-50.0)
    assert roe_zero is None
    assert roe_neg is None


def test_roce_normal():
    """Test ROCE calculation under normal conditions."""
    roce = calculate_roce(ebit=250.0, equity_capital=50.0, reserves=450.0, borrowings=500.0)
    assert roce == pytest.approx(25.0)


def test_roa_normal_and_zero_assets():
    """Test ROA calculation under normal and zero asset conditions."""
    roa = calculate_roa(net_profit=80.0, total_assets=800.0)
    assert roa == pytest.approx(10.0)

    roa_zero = calculate_roa(net_profit=80.0, total_assets=0.0)
    assert roa_zero is None


def test_book_value_per_share():
    """Test Book Value per Share (BVPS) calculation using derived shares."""
    # Equity = 100 Cr, Net Profit = 20 Cr, EPS = 5 Rs
    # Derived Shares = 20 Cr / 5 Rs = 4 Cr shares
    # BVPS = 100 Cr / 4 Cr = 25 Rs
    bvps = calculate_book_value_per_share(equity_capital=10.0, reserves=90.0, net_profit=20.0, eps=5.0)
    assert bvps == pytest.approx(25.0)

    # Missing inputs or zero/negative net_profit or eps -> None
    assert calculate_book_value_per_share(10.0, 90.0, 0.0, 5.0) is None
    assert calculate_book_value_per_share(10.0, 90.0, 20.0, None) is None

