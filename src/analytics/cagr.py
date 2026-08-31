"""
CAGR Engine.
Computes multi-year Compound Annual Growth Rates for Revenue, PAT, and EPS.
Handles 6 edge cases with explicit flags:
- NORMAL
- DECLINE_TO_LOSS
- TURNAROUND
- BOTH_NEGATIVE
- ZERO_BASE
- INSUFFICIENT
"""

from typing import Optional, Tuple, Dict, List


def calculate_cagr(
    start_val: Optional[float],
    end_val: Optional[float],
    n_years: int
) -> Tuple[Optional[float], str]:
    """
    Compute Compound Annual Growth Rate (CAGR) between two points.
    Formula: ((end_val / start_val) ** (1 / n_years) - 1) * 100

    Returns (cagr_val, flag).
    """
    if n_years <= 0:
        return None, "INSUFFICIENT"

    if start_val is None or end_val is None:
        return None, "INSUFFICIENT"

    if start_val == 0:
        return None, "ZERO_BASE"

    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"

    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"

    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"

    # Both positive
    if start_val > 0 and end_val >= 0:
        try:
            cagr_val = (((end_val / start_val) ** (1.0 / n_years)) - 1.0) * 100.0
            return cagr_val, "NORMAL"
        except (ValueError, ZeroDivisionError, OverflowError):
            return None, "INSUFFICIENT"

    return None, "INSUFFICIENT"


def calculate_series_cagr(
    year_val_map: Dict[int, float],
    target_year: int,
    n_years: int
) -> Tuple[Optional[float], str]:
    """
    Compute CAGR for a specific target_year over an n_years window
    using a dictionary mapping year -> numeric value.
    Validates actual historical year presence (start_year = target_year - n_years).
    """
    start_year = target_year - n_years

    if target_year not in year_val_map or start_year not in year_val_map:
        return None, "INSUFFICIENT"

    start_val = year_val_map[start_year]
    end_val = year_val_map[target_year]

    return calculate_cagr(start_val, end_val, n_years)
