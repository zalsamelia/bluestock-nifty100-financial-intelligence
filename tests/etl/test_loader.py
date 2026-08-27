"""
Unit tests for src.etl.loader module.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.etl.loader import (
    load_excel,
    normalize_columns,
    normalize_dataframe,
    load_and_normalize,
    get_project_root,
    get_raw_data_path,
)


def test_normalize_columns_basic():
    """Test column name normalization transforms whitespace, case, and underscores."""
    df = pd.DataFrame(columns=["  Company Ticker  ", "Financial Year ", "Total Assets (Cr)"])
    normalized = normalize_columns(df)
    assert list(normalized.columns) == ["company_ticker", "financial_year", "total_assets_(cr)"]


def test_normalize_columns_multiple_underscores():
    """Test that multiple spaces or underscores are collapsed."""
    df = pd.DataFrame(columns=["Net   Sales", "  Op__Profit  "])
    normalized = normalize_columns(df)
    assert list(normalized.columns) == ["net_sales", "op_profit"]


def test_normalize_dataframe_tickers_and_years():
    """Test normalize_dataframe applies ticker and year normalization to matching columns."""
    df = pd.DataFrame({
        "ticker": ["  reliance  ", "tcs  ", "INFY"],
        "year": ["FY2023", "FY 2024", "FY 2022"],
        "sales": [100, 200, 300]
    })
    result = normalize_dataframe(df)
    assert list(result["ticker"]) == ["RELIANCE", "TCS", "INFY"]
    assert list(result["year"]) == [2023, 2024, 2022]


def test_get_project_root_and_data_path():
    """Test project root and raw data path helper functions."""
    root = get_project_root()
    raw_path = get_raw_data_path()
    assert isinstance(root, Path)
    assert isinstance(raw_path, Path)
    assert raw_path == root / "data" / "raw"


def test_load_excel_non_existent():
    """Test load_excel raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_excel("non_existent_file.xlsx")


def test_load_excel_invalid_extension():
    """Test load_excel raises ValueError for unsupported extensions."""
    tmp_file = get_project_root() / "test_temp.txt"
    tmp_file.write_text("hello")
    try:
        with pytest.raises(ValueError):
            load_excel(tmp_file)
    finally:
        if tmp_file.exists():
            tmp_file.unlink()
