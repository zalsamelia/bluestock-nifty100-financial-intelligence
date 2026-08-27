import pandas as pd

from src.etl.normaliser import normalize_dataframe


def test_normalize_dataframe_ticker():
    df = pd.DataFrame({
        "company_id": ["reliance", " tcs ", "HDFCBANK"]
    })

    result = normalize_dataframe(
        df,
        ticker_column="company_id"
    )

    assert result["company_id"].tolist() == [
        "RELIANCE",
        "TCS",
        "HDFCBANK"
    ]


def test_normalize_dataframe_year():
    df = pd.DataFrame({
        "year": ["FY2023", "Mar 2024", "2025-26"]
    })

    result = normalize_dataframe(
        df,
        year_column="year"
    )

    assert result["year"].tolist() == [
        2023,
        2024,
        2025
    ]