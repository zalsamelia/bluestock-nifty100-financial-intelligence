"""
Unit Tests for Cash Flow KPIs and Capital Allocation Classifier (Day 11).
"""

import pytest
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
)


def test_free_cash_flow():
    """Test FCF calculation (negative values allowed)."""
    fcf_pos = calculate_free_cash_flow(cfo=1500.0, cfi=-800.0)
    assert fcf_pos == pytest.approx(700.0)

    fcf_neg = calculate_free_cash_flow(cfo=500.0, cfi=-1200.0)
    assert fcf_neg == pytest.approx(-700.0)


def test_cfo_quality_score():
    """Test 5-year CFO Quality Score and labels."""
    # > 1.0 -> High Quality
    score_hq, label_hq = calculate_cfo_quality([1.2, 1.1, 1.3, 1.0, 1.4])
    assert score_hq == pytest.approx(1.2)
    assert label_hq == "High Quality"

    # 0.5 - 1.0 -> Moderate
    score_mod, label_mod = calculate_cfo_quality([0.8, 0.7, 0.9, 0.6, 0.8])
    assert score_mod == pytest.approx(0.76)
    assert label_mod == "Moderate"

    # < 0.5 -> Accrual Risk
    score_risk, label_risk = calculate_cfo_quality([0.3, 0.4, 0.2, 0.1, 0.5])
    assert score_risk == pytest.approx(0.3)
    assert label_risk == "Accrual Risk"


def test_capex_intensity():
    """Test CapEx Intensity calculation and labels."""
    # < 3% -> Asset Light
    pct_light, label_light = calculate_capex_intensity(cfi=-20.0, sales=1000.0)
    assert pct_light == pytest.approx(2.0)
    assert label_light == "Asset Light"

    # 3% - 8% -> Moderate
    pct_mod, label_mod = calculate_capex_intensity(cfi=-50.0, sales=1000.0)
    assert pct_mod == pytest.approx(5.0)
    assert label_mod == "Moderate"

    # > 8% -> Capital Intensive
    pct_ci, label_ci = calculate_capex_intensity(cfi=-150.0, sales=1000.0)
    assert pct_ci == pytest.approx(15.0)
    assert label_ci == "Capital Intensive"


def test_fcf_conversion():
    """Test FCF Conversion calculation and zero operating profit edge case."""
    conv = calculate_fcf_conversion(fcf=600.0, operating_profit=1000.0)
    assert conv == pytest.approx(60.0)

    conv_zero = calculate_fcf_conversion(fcf=600.0, operating_profit=0.0)
    assert conv_zero is None


def test_capital_allocation_patterns():
    """Test 8-pattern capital allocation classifier."""
    # (+,-,-) with CFO/PAT > 1.0 -> Shareholder Returns
    s1, s2, s3, l1 = classify_capital_allocation(cfo=100, cfi=-50, cff=-20, cfo_pat_ratio=1.2)
    assert (s1, s2, s3) == ("+", "-", "-")
    assert l1 == "Shareholder Returns"

    # (+,-,-) default -> Reinvestor
    _, _, _, l2 = classify_capital_allocation(cfo=100, cfi=-50, cff=-20, cfo_pat_ratio=0.8)
    assert l2 == "Reinvestor"

    # (+,+,-) -> Liquidating Assets
    _, _, _, l3 = classify_capital_allocation(cfo=100, cfi=50, cff=-20)
    assert l3 == "Liquidating Assets"

    # (-,+,+) -> Distress Signal
    _, _, _, l4 = classify_capital_allocation(cfo=-50, cfi=30, cff=40)
    assert l4 == "Distress Signal"

    # (-,-,+) -> Growth Funded by Debt
    _, _, _, l5 = classify_capital_allocation(cfo=-50, cfi=-30, cff=40)
    assert l5 == "Growth Funded by Debt"

    # (+,+,+) -> Cash Accumulator
    _, _, _, l6 = classify_capital_allocation(cfo=100, cfi=50, cff=20)
    assert l6 == "Cash Accumulator"

    # (-,-,-) -> Pre-Revenue
    _, _, _, l7 = classify_capital_allocation(cfo=-10, cfi=-20, cff=-30)
    assert l7 == "Pre-Revenue"

    # (+,-,+) -> Mixed
    _, _, _, l8 = classify_capital_allocation(cfo=100, cfi=-50, cff=20)
    assert l8 == "Mixed"
