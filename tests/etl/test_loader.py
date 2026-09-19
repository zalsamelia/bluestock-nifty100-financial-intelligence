"""
Unit tests for src.etl.loader module (10 tests).
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
    df = pd.DataFrame(columns=["  Company Ticker  ", "Financial Year ", "Total Assets (Cr)"])
    normalized = normalize_columns(df)
    assert list(normalized.columns) == ["company_ticker", "financial_year", "total_assets_(cr)"]

def test_normalize_columns_multiple_underscores():
    df = pd.DataFrame(columns=["Net   Sales", "  Op__Profit  "])
    normalized = normalize_columns(df)
    assert list(normalized.columns) == ["net_sales", "op_profit"]

def test_normalize_columns_special_symbols():
    df = pd.DataFrame(columns=["PAT %", "Debt/Equity", "ROE %"])
    normalized = normalize_columns(df)
    assert len(normalized.columns) == 3
    assert all(isinstance(c, str) for c in normalized.columns)

def test_normalize_dataframe_tickers_and_years():
    df = pd.DataFrame({
        "ticker": ["  reliance  ", "tcs  ", "INFY"],
        "year": ["FY2023", "FY 2024", "FY 2022"],
        "sales": [100, 200, 300]
    })
    result = normalize_dataframe(df)
    assert list(result["ticker"]) == ["RELIANCE", "TCS", "INFY"]
    assert list(result["year"]) == [2023, 2024, 2022]

def test_normalize_dataframe_empty():
    df = pd.DataFrame()
    result = normalize_dataframe(df)
    assert result.empty

def test_get_project_root_type():
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_raw_data_path():
    raw_path = get_raw_data_path()
    assert isinstance(raw_path, Path)
    assert "data" in str(raw_path)

def test_load_excel_non_existent():
    with pytest.raises(FileNotFoundError):
        load_excel("non_existent_file_12345.xlsx")

def test_load_excel_invalid_extension():
    tmp_file = get_project_root() / "test_temp_invalid.txt"
    tmp_file.write_text("dummy")
    try:
        with pytest.raises(ValueError):
            load_excel(tmp_file)
    finally:
        if tmp_file.exists():
            tmp_file.unlink()

def test_load_and_normalize_missing():
    with pytest.raises(FileNotFoundError):
        load_and_normalize("non_existent_path.xlsx")
