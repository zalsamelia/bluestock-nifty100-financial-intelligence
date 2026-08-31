"""
Profitability, Leverage, and Efficiency Ratio Calculations.
Handles edge cases: zero denominators, negative equity, debt-free companies,
and bank leverage carve-outs.
"""

from typing import Optional, Tuple, Dict, Any


def calculate_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Compute Net Profit Margin (NPM).
    NPM = net_profit / sales * 100
    Returns None if sales is 0 or None.
    """
    if sales is None or sales == 0 or net_profit is None:
        return None
    return (net_profit / sales) * 100.0


def calculate_opm(
    operating_profit: Optional[float],
    sales: Optional[float],
    source_opm: Optional[float] = None
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """
    Compute Operating Profit Margin (OPM).
    OPM = operating_profit / sales * 100
    Cross-checks against source_opm and detects mismatches > 1%.
    Returns (computed_opm, mismatch_info).
    """
    if sales is None or sales == 0 or operating_profit is None:
        return None, None

    computed_opm = (operating_profit / sales) * 100.0

    mismatch_info = None
    if source_opm is not None:
        diff = abs(computed_opm - source_opm)
        if diff > 1.0:
            mismatch_info = {
                "computed_opm": computed_opm,
                "source_opm": source_opm,
                "difference": diff
            }

    return computed_opm, mismatch_info


def calculate_roe(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float]
) -> Optional[float]:
    """
    Compute Return on Equity (ROE).
    ROE = net_profit / (equity_capital + reserves) * 100
    Returns None if equity_capital + reserves <= 0 or inputs are missing.
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None

    equity_total = equity_capital + reserves
    if equity_total <= 0:
        return None

    return (net_profit / equity_total) * 100.0


def calculate_roce(
    ebit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float]
) -> Optional[float]:
    """
    Compute Return on Capital Employed (ROCE).
    ROCE = EBIT / (equity_capital + reserves + borrowings) * 100
    Returns None if capital employed <= 0 or inputs are missing.
    """
    if ebit is None or equity_capital is None or reserves is None or borrowings is None:
        return None

    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100.0


def calculate_roa(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Compute Return on Assets (ROA).
    ROA = net_profit / total_assets * 100
    Returns None if total_assets is 0 or None.
    """
    if net_profit is None or total_assets is None or total_assets == 0:
        return None

    return (net_profit / total_assets) * 100.0


def calculate_debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    is_financial_sector: bool = False
) -> Tuple[Optional[float], bool]:
    """
    Compute Debt-to-Equity (D/E) ratio and high leverage flag.
    D/E = borrowings / (equity_capital + reserves)
    Returns 0.0 (not None) if borrowings == 0.
    High leverage flag = True if D/E > 5 and company is NOT in Financials sector.
    Returns (debt_to_equity, high_leverage_flag).
    """
    if borrowings is None or borrowings == 0:
        return 0.0, False

    if equity_capital is None or reserves is None:
        return None, False

    equity_total = equity_capital + reserves
    if equity_total <= 0:
        return None, False

    de_ratio = borrowings / equity_total
    high_leverage_flag = (not is_financial_sector) and (de_ratio > 5.0)

    return de_ratio, high_leverage_flag


def calculate_interest_coverage(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Compute Interest Coverage Ratio (ICR).
    ICR = (operating_profit + other_income) / interest
    If interest == 0 or None: returns (None, "Debt Free", False).
    If ICR < 1.5: returns (ICR, None, True) indicating ICR warning flag.
    Returns (icr_value, icr_label, icr_warning_flag).
    """
    if interest is None or interest == 0:
        return None, "Debt Free", False

    op_profit = operating_profit if operating_profit is not None else 0.0
    oth_inc = other_income if other_income is not None else 0.0
    total_operating_earnings = op_profit + oth_inc

    icr_value = total_operating_earnings / interest
    icr_warning_flag = icr_value < 1.5

    return icr_value, None, icr_warning_flag


def calculate_net_debt(borrowings: Optional[float], investments: Optional[float]) -> Optional[float]:
    """
    Compute Net Debt.
    Net Debt = borrowings - investments (using investments as liquid asset proxy).
    """
    if borrowings is None and investments is None:
        return None
    borr = borrowings if borrowings is not None else 0.0
    inv = investments if investments is not None else 0.0
    return borr - inv


def calculate_asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Compute Asset Turnover.
    Asset Turnover = sales / total_assets
    Returns None if total_assets is 0 or None.
    """
    if sales is None or total_assets is None or total_assets == 0:
        return None

    return sales / total_assets


def calculate_book_value_per_share(
    equity_capital: Optional[float],
    reserves: Optional[float],
    net_profit: Optional[float],
    eps: Optional[float]
) -> Optional[float]:
    """
    Compute Book Value per Share (BVPS).
    BVPS = Total Equity / Shares Outstanding
    Where Shares Outstanding = Net Profit / EPS (derived when shares is not explicit).
    Returns None if equity <= 0, net_profit <= 0, or eps <= 0 / missing.
    """
    if equity_capital is None or reserves is None:
        return None

    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None

    if net_profit is None or eps is None or net_profit <= 0 or eps <= 0:
        return None

    derived_shares_cr = net_profit / eps
    return (total_equity / derived_shares_cr)

