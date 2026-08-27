"""
Normalization utilities for Nifty100 Financial Intelligence ETL pipeline.
"""

import re
from typing import Any, Optional

import pandas as pd


def normalize_year(value: Any) -> Optional[int]:
    """
    Normalize different financial-year representations into a calendar year.

    Examples:
        2023                 -> 2023
        2023.0               -> 2023
        "FY2023"             -> 2023
        "FY 2023"            -> 2023
        "FY-2023"            -> 2023
        "FY2023-24"          -> 2023
        "2023-24"            -> 2023
        "Mar 2024"           -> 2024
        "Financial Year 2023" -> 2023

    Invalid or missing values return None.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "n/a", "na", "-"}:
        return None

    match = re.search(r"(20\d{2})", text)

    if not match:
        return None

    return int(match.group(1))


def normalize_ticker(value: Any) -> Optional[str]:
    """
    Normalize company ticker symbols.

    Examples:
        "reliance"       -> "RELIANCE"
        " TCS "          -> "TCS"
        "icici bank"     -> "ICICI BANK"
        None             -> None
        ""               -> None
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "n/a", "na", "-"}:
        return None

    return text.upper()


def normalize_dataframe(
    df: pd.DataFrame,
    ticker_column: str | None = None,
    year_column: str | None = None,
) -> pd.DataFrame:
    """
    Apply ticker and year normalization to a DataFrame.

    If ticker_column or year_column is not explicitly provided,
    the function attempts to detect common column names automatically.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    ticker_column : str | None
        Column containing company ticker symbols.

    year_column : str | None
        Column containing financial-year values.

    Returns
    -------
    pd.DataFrame
        Copy of the DataFrame with normalized ticker and year columns.
    """

    df = df.copy()

    # ----------------------------------------------------------
    # Detect ticker column
    # ----------------------------------------------------------

    if ticker_column is None:
        ticker_candidates = [
            "company_id",
            "ticker",
            "symbol",
            "stock_code",
        ]

        for column in ticker_candidates:
            if column in df.columns:
                ticker_column = column
                break

    # ----------------------------------------------------------
    # Detect year column
    # ----------------------------------------------------------

    if year_column is None:
        year_candidates = [
            "year",
            "Year",
            "financial_year",
            "fiscal_year",
        ]

        for column in year_candidates:
            if column in df.columns:
                year_column = column
                break

    # ----------------------------------------------------------
    # Normalize ticker
    # ----------------------------------------------------------

    if ticker_column and ticker_column in df.columns:
        df[ticker_column] = df[ticker_column].apply(normalize_ticker)

    # ----------------------------------------------------------
    # Normalize year
    # ----------------------------------------------------------

    if year_column and year_column in df.columns:
        df[year_column] = df[year_column].apply(normalize_year)

    return df