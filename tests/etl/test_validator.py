import pandas as pd

from src.etl.validator import DataValidator


def test_dq01_primary_key_uniqueness_passes():
    df = pd.DataFrame(
        {
            "company_id": ["A", "B", "C"],
        }
    )

    validator = DataValidator()

    validator.check_primary_key_uniqueness(
        df=df,
        table="companies",
        columns=["company_id"],
    )

    assert validator.get_failures().empty


def test_dq01_primary_key_uniqueness_detects_duplicates():
    df = pd.DataFrame(
        {
            "company_id": ["A", "A", "B"],
        }
    )

    validator = DataValidator()

    validator.check_primary_key_uniqueness(
        df=df,
        table="companies",
        columns=["company_id"],
    )

    failures = validator.get_failures()

    assert len(failures) == 1
    assert failures.iloc[0]["rule_id"] == "DQ-01"
    assert failures.iloc[0]["severity"] == "CRITICAL"
    assert failures.iloc[0]["row_count"] == 2


def test_dq02_company_year_uniqueness_passes():
    df = pd.DataFrame(
        {
            "company_id": ["A", "A", "B"],
            "year": [2022, 2023, 2022],
        }
    )

    validator = DataValidator()

    validator.check_company_year_uniqueness(
        df=df,
        table="profitandloss",
    )

    assert validator.get_failures().empty


def test_dq02_company_year_uniqueness_detects_duplicates():
    df = pd.DataFrame(
        {
            "company_id": ["A", "A", "B"],
            "year": [2022, 2022, 2022],
        }
    )

    validator = DataValidator()

    validator.check_company_year_uniqueness(
        df=df,
        table="profitandloss",
    )

    failures = validator.get_failures()

    assert len(failures) == 1
    assert failures.iloc[0]["rule_id"] == "DQ-02"
    assert failures.iloc[0]["severity"] == "CRITICAL"
    assert failures.iloc[0]["row_count"] == 2


def test_dq03_foreign_key_integrity_passes():
    companies = pd.DataFrame(
        {
            "company_id": ["A", "B", "C"],
        }
    )

    profitandloss = pd.DataFrame(
        {
            "company_id": ["A", "B"],
            "year": [2022, 2022],
        }
    )

    validator = DataValidator()

    validator.check_foreign_key_integrity(
        child_df=profitandloss,
        parent_df=companies,
        child_table="profitandloss",
    )

    assert validator.get_failures().empty


def test_dq03_foreign_key_integrity_detects_invalid_keys():
    companies = pd.DataFrame(
        {
            "company_id": ["A", "B"],
        }
    )

    profitandloss = pd.DataFrame(
        {
            "company_id": ["A", "B", "C"],
            "year": [2022, 2022, 2022],
        }
    )

    validator = DataValidator()

    validator.check_foreign_key_integrity(
        child_df=profitandloss,
        parent_df=companies,
        child_table="profitandloss",
    )

    failures = validator.get_failures()

    assert len(failures) == 1
    assert failures.iloc[0]["rule_id"] == "DQ-03"
    assert failures.iloc[0]["severity"] == "CRITICAL"
    assert failures.iloc[0]["row_count"] == 1

def test_dq04_balance_sheet_balance_passes():
    df = pd.DataFrame(
        {
            "total_assets": [1000, 2000],
            "total_liabilities": [995, 1990],
        }
    )

    validator = DataValidator()

    validator.check_balance_sheet_balance(
        df=df,
        table="balancesheet",
    )

    assert validator.get_failures().empty


def test_dq04_balance_sheet_balance_detects_failure():
    df = pd.DataFrame(
        {
            "total_assets": [1000, 2000],
            "total_liabilities": [900, 1990],
        }
    )

    validator = DataValidator()

    validator.check_balance_sheet_balance(
        df=df,
        table="balancesheet",
    )

    failures = validator.get_failures()

    assert len(failures) == 1
    assert failures.iloc[0]["rule_id"] == "DQ-04"
    assert failures.iloc[0]["severity"] == "WARNING"
    assert failures.iloc[0]["row_count"] == 1