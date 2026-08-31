"""
Cash Flow KPIs and Capital Allocation Pattern Classifier.
Implements FCF, CFO Quality Score, CapEx Intensity, FCF Conversion,
and 8-pattern Capital Allocation classifier.
"""

from typing import Optional, Tuple, List


def calculate_free_cash_flow(
    cfo: Optional[float],
    cfi: Optional[float]
) -> Optional[float]:
    """
    Compute Free Cash Flow (FCF).
    FCF = CFO + CFI (operating_activity + investing_activity)
    Negative value is allowed.
    """
    if cfo is None or cfi is None:
        return None
    return cfo + cfi


def calculate_cfo_quality(
    cfo_pat_ratios: List[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute CFO Quality Score based on average CFO/PAT ratio over up to 5 years.
    - > 1.0  : High Quality
    - 0.5-1.0: Moderate
    - < 0.5  : Accrual Risk
    Returns (avg_score, label).
    """
    valid_ratios = [r for r in cfo_pat_ratios if r is not None]
    if not valid_ratios:
        return None, None

    avg_score = sum(valid_ratios) / len(valid_ratios)

    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label


def calculate_capex_intensity(
    cfi: Optional[float],
    sales: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute CapEx Intensity: abs(investing_activity) / sales * 100.
    Classification:
    - < 3%  : Asset Light
    - 3-8%  : Moderate
    - > 8%  : Capital Intensive
    Returns (capex_pct, label).
    """
    if cfi is None or sales is None or sales == 0:
        return None, None

    capex_pct = (abs(cfi) / sales) * 100.0

    if capex_pct < 3.0:
        label = "Asset Light"
    elif capex_pct <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return capex_pct, label


def calculate_fcf_conversion(
    fcf: Optional[float],
    operating_profit: Optional[float]
) -> Optional[float]:
    """
    Compute FCF Conversion Rate: FCF / operating_profit * 100.
    Returns None if operating_profit is 0 or None.
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classify capital allocation into one of 8 patterns based on (CFO, CFI, CFF) signs:
    - (+,-,-) with CFO/PAT > 1.0 -> Shareholder Returns
    - (+,-,-) default            -> Reinvestor
    - (+,+,-)                    -> Liquidating Assets
    - (-,+,+)                    -> Distress Signal
    - (-,-,+)                    -> Growth Funded by Debt
    - (+,+,+)                    -> Cash Accumulator
    - (-,-,-)                    -> Pre-Revenue
    - (+,-,+)                    -> Mixed

    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    if cfo is None:
        cfo = 0.0
    if cfi is None:
        cfi = 0.0
    if cff is None:
        cff = 0.0

    cfo_sign = "+" if cfo > 0 else "-"
    cfi_sign = "+" if cfi > 0 else "-"
    cff_sign = "+" if cff > 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        label = "Mixed"
    else:
        label = "Mixed"

    return cfo_sign, cfi_sign, cff_sign, label
