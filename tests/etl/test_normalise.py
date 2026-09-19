"""
Unit tests for data normalization (20 test cases).
Covers year formats, ticker strings, edge cases, nulls, and dataframe transformations.
"""

import math
import numpy as np
import pandas as pd
import pytest
from src.etl.normaliser import normalize_year, normalize_ticker, normalize_dataframe


# --- Year Normalization Tests (10 tests) ---

def test_normalize_year_standard_int():
    assert normalize_year(2023) == 2023

def test_normalize_year_float():
    assert normalize_year(2022.0) == 2022

def test_normalize_year_fy_prefix():
    assert normalize_year("FY2023") == 2023

def test_normalize_year_fy_space():
    assert normalize_year("FY 2024") == 2024

def test_normalize_year_fy_hyphen():
    assert normalize_year("FY-2021") == 2021

def test_normalize_year_range():
    assert normalize_year("FY2023-24") == 2023

def test_normalize_year_month_year():
    assert normalize_year("Mar 2024") == 2024

def test_normalize_year_long_text():
    assert normalize_year("Financial Year 2020") == 2020

def test_normalize_year_none():
    assert normalize_year(None) is None

def test_normalize_year_invalid_strings():
    for val in ["", "nan", "NaN", "None", "N/A", "na", "-", "Unknown"]:
        assert normalize_year(val) is None


# --- Ticker Normalization Tests (6 tests) ---

def test_normalize_ticker_lowercase():
    assert normalize_ticker("reliance") == "RELIANCE"

def test_normalize_ticker_whitespace():
    assert normalize_ticker("  TCS  ") == "TCS"

def test_normalize_ticker_multiword():
    assert normalize_ticker("icici bank") == "ICICI BANK"

def test_normalize_ticker_none():
    assert normalize_ticker(None) is None

def test_normalize_ticker_empty():
    assert normalize_ticker("") is None
    assert normalize_ticker("   ") is None

def test_normalize_ticker_special_chars():
    assert normalize_ticker("m_and_m") == "M_AND_M"
    assert normalize_ticker("lt") == "LT"


# --- DataFrame Normalization Tests (4 tests) ---

def test_normalize_dataframe_explicit_columns():
    df = pd.DataFrame({
        "symbol": ["infy", "wipro"],
        "period": ["FY 2022", "FY 2023"],
        "val": [10, 20]
    })
    res = normalize_dataframe(df, ticker_column="symbol", year_column="period")
    assert list(res["symbol"]) == ["INFY", "WIPRO"]
    assert list(res["period"]) == [2022, 2023]

def test_normalize_dataframe_auto_detect():
    df = pd.DataFrame({
        "ticker": ["tcs", "hcltech"],
        "year": ["FY2021", "FY2022"]
    })
    res = normalize_dataframe(df)
    assert list(res["ticker"]) == ["TCS", "HCLTECH"]
    assert list(res["year"]) == [2021, 2022]

def test_normalize_dataframe_missing_values():
    df = pd.DataFrame({
        "ticker": ["tcs", None, "   "],
        "year": ["FY2021", "-", "None"]
    })
    res = normalize_dataframe(df)
    assert res["ticker"].iloc[0] == "TCS"
    assert pd.isna(res["ticker"].iloc[1])
    assert pd.isna(res["ticker"].iloc[2])
    assert res["year"].iloc[0] == 2021
    assert pd.isna(res["year"].iloc[1])
    assert pd.isna(res["year"].iloc[2])

def test_normalize_dataframe_immutability():
    df = pd.DataFrame({
        "ticker": ["tcs"],
        "year": ["FY2021"]
    })
    res = normalize_dataframe(df)
    assert df["ticker"].iloc[0] == "tcs"
    assert res["ticker"].iloc[0] == "TCS"
