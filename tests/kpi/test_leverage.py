"""
Unit Tests for Leverage & Efficiency Ratios (Day 09).
"""

import pytest
from src.analytics.ratios import (
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
)


def test_de_debt_free_returns_zero():
    """Test Debt-to-Equity returns 0.0 (not None) when borrowings == 0."""
    de, flag = calculate_debt_to_equity(borrowings=0.0, equity_capital=100.0, reserves=400.0)
    assert de == 0.0
    assert flag is False


def test_de_high_leverage_flag():
    """Test high leverage flag (> 5) for non-financial companies."""
    de, flag = calculate_debt_to_equity(
        borrowings=600.0,
        equity_capital=20.0,
        reserves=80.0,
        is_financial_sector=False
    )
    assert de == pytest.approx(6.0)
    assert flag is True


def test_de_financials_carveout():
    """Test high leverage flag is suppressed for Financials broad_sector."""
    de, flag = calculate_debt_to_equity(
        borrowings=1000.0,
        equity_capital=20.0,
        reserves=80.0,
        is_financial_sector=True
    )
    assert de == pytest.approx(10.0)
    assert flag is False  # Suppressed for Financials


def test_icr_interest_zero_returns_none_and_label():
    """Test ICR returns None and label 'Debt Free' when interest == 0."""
    icr, label, warning = calculate_interest_coverage(
        operating_profit=500.0,
        other_income=50.0,
        interest=0.0
    )
    assert icr is None
    assert label == "Debt Free"
    assert warning is False


def test_icr_warning_flag():
    """Test ICR warning flag triggers when ICR < 1.5."""
    icr, label, warning = calculate_interest_coverage(
        operating_profit=100.0,
        other_income=20.0,
        interest=100.0
    )
    assert icr == pytest.approx(1.2)
    assert label is None
    assert warning is True


def test_net_debt_calculation():
    """Test Net Debt calculation = borrowings - investments."""
    net_debt = calculate_net_debt(borrowings=500.0, investments=200.0)
    assert net_debt == pytest.approx(300.0)


def test_asset_turnover():
    """Test Asset Turnover calculation and zero asset edge case."""
    turnover = calculate_asset_turnover(sales=1200.0, total_assets=600.0)
    assert turnover == pytest.approx(2.0)

    turnover_zero = calculate_asset_turnover(sales=1200.0, total_assets=0.0)
    assert turnover_zero is None
