"""
Unit tests for KPI ratios calculations covering 20 edge cases.
(Negative denominator, zero debt, high growth, null values, division by zero, etc.)
"""

import math
import numpy as np
import pytest

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_opm,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
    calculate_book_value_per_share,
)
from src.analytics.cagr import calculate_cagr

# 1. Operating Margin standard
def test_calculate_opm_standard():
    opm, mismatch = calculate_opm(250.0, 1000.0)
    assert opm == 25.0
    assert mismatch is None

# 2. Operating Margin zero sales
def test_calculate_opm_zero_sales():
    opm, mismatch = calculate_opm(250.0, 0.0)
    assert opm is None

# 3. Operating Margin with source mismatch check
def test_calculate_opm_mismatch():
    opm, mismatch = calculate_opm(250.0, 1000.0, source_opm=20.0)
    assert opm == 25.0
    assert mismatch is not None
    assert mismatch["difference"] == 5.0

# 4. Net Margin standard
def test_calculate_net_margin_standard():
    npm = calculate_net_profit_margin(150.0, 1000.0)
    assert npm == 15.0

# 5. Net Margin null inputs
def test_calculate_net_margin_nulls():
    assert calculate_net_profit_margin(None, 1000.0) is None
    assert calculate_net_profit_margin(150.0, None) is None

# 6. ROE standard
def test_calculate_roe_standard():
    roe = calculate_roe(25.0, 10.0, 90.0)
    assert roe == 25.0

# 7. ROE negative equity (reserves wipe out capital)
def test_calculate_roe_negative_equity():
    roe = calculate_roe(25.0, 10.0, -50.0)
    assert roe is None

# 8. ROE zero equity
def test_calculate_roe_zero_equity():
    roe = calculate_roe(25.0, 0.0, 0.0)
    assert roe is None

# 9. ROCE standard
def test_calculate_roce_standard():
    # EBIT = 30, Equity=10, Reserves=90, Borrowings=50 -> Capital Employed = 150 -> 30/150 = 20%
    roce = calculate_roce(30.0, 10.0, 90.0, 50.0)
    assert roce == 20.0

# 10. ROCE missing inputs
def test_calculate_roce_missing():
    assert calculate_roce(None, 10.0, 90.0, 50.0) is None
    assert calculate_roce(30.0, 10.0, 90.0, None) is None

# 11. ROA standard
def test_calculate_roa_standard():
    roa = calculate_roa(50.0, 1000.0)
    assert roa == 5.0

# 12. ROA zero assets
def test_calculate_roa_zero_assets():
    assert calculate_roa(50.0, 0.0) is None

# 13. Debt to Equity zero debt (debt-free company)
def test_calculate_debt_to_equity_zero_debt():
    de, high_lev = calculate_debt_to_equity(0.0, 10.0, 90.0)
    assert de == 0.0
    assert not high_lev

# 14. Debt to Equity high leverage non-financial
def test_calculate_debt_to_equity_high_leverage():
    de, high_lev = calculate_debt_to_equity(600.0, 10.0, 90.0, is_financial_sector=False)
    assert de == 6.0
    assert high_lev is True

# 15. Debt to Equity high leverage financial sector exemption
def test_calculate_debt_to_equity_financial_exemption():
    de, high_lev = calculate_debt_to_equity(600.0, 10.0, 90.0, is_financial_sector=True)
    assert de == 6.0
    assert high_lev is False

# 16. Interest Coverage standard
def test_calculate_interest_coverage_standard():
    icr, label, flag = calculate_interest_coverage(80.0, 20.0, 20.0)
    assert icr == 5.0
    assert label is None
    assert flag is False

# 17. Interest Coverage zero interest (debt-free label)
def test_calculate_interest_coverage_debt_free():
    icr, label, flag = calculate_interest_coverage(100.0, 10.0, 0.0)
    assert icr is None
    assert label == "Debt Free"
    assert flag is False

# 18. Asset Turnover standard
def test_calculate_asset_turnover_standard():
    at = calculate_asset_turnover(2000.0, 1000.0)
    assert at == 2.0

# 19. CAGR standard positive growth
def test_calculate_cagr_positive():
    val, flag = calculate_cagr(100.0, 200.0, 3)
    assert round(val, 2) == 25.99
    assert flag == "NORMAL"

# 20. CAGR decline to loss turnaround
def test_calculate_cagr_decline_to_loss():
    val, flag = calculate_cagr(100.0, -50.0, 3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"
