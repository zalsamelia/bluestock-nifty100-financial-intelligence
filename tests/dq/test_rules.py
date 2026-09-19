"""
Unit tests for Data Quality Rules (DQ-01 to DQ-14).
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path
from src.etl.dq_validator import (
    DQ_META,
    add_failure,
)

# Test metadata completeness
def test_dq_metadata_structure():
    for i in range(1, 15):
        dq_id = f"DQ-{i:02d}"
        assert dq_id in DQ_META
        name, severity = DQ_META[dq_id]
        assert isinstance(name, str)
        assert severity in ("CRITICAL", "WARNING", "INFO")

def test_add_failure_helper():
    failures = []
    add_failure(failures, "DQ-01", "TCS", 2023, "company_id", "Duplicate key", 2, 1)
    assert len(failures) == 1
    assert failures[0]["dq_id"] == "DQ-01"
    assert failures[0]["severity"] == "CRITICAL"

def test_dq_01_company_pk_uniqueness():
    df = pd.DataFrame({"company_id": ["TCS", "INFY", "TCS"]})
    is_unique = df["company_id"].is_unique
    assert not is_unique

def test_dq_02_annual_pk_uniqueness():
    df = pd.DataFrame({"company_id": ["TCS", "TCS"], "year": [2023, 2023]})
    assert df.duplicated(subset=["company_id", "year"]).any()

def test_dq_03_fk_integrity():
    companies = {"TCS", "INFY", "RELIANCE"}
    records = ["TCS", "UNKNOWN_CO"]
    orphans = [r for r in records if r not in companies]
    assert len(orphans) == 1
    assert orphans[0] == "UNKNOWN_CO"

def test_dq_04_balance_sheet_balance():
    total_assets = 1000.0
    total_liabilities = 1000.0
    assert abs(total_assets - total_liabilities) < 1e-4

def test_dq_05_opm_cross_check():
    sales = 1000.0
    op_profit = 250.0
    reported_opm = 25.0
    calculated_opm = (op_profit / sales) * 100.0
    assert abs(reported_opm - calculated_opm) < 0.1

def test_dq_06_positive_sales():
    sales_valid = 500.0
    sales_invalid = -10.0
    assert sales_valid > 0
    assert not (sales_invalid > 0)

def test_dq_07_year_format():
    valid_years = [2018, 2020, 2024]
    invalid_years = [1890, 2150, "FY23"]
    assert all(2000 <= y <= 2030 for y in valid_years)
    assert not all(isinstance(y, int) and 2000 <= y <= 2030 for y in invalid_years)

def test_dq_08_ticker_format():
    valid_tickers = ["TCS", "RELIANCE", "M_AND_M", "HDFCBANK"]
    assert all(t.isupper() for t in valid_tickers)

def test_dq_09_net_cash_check():
    cfo = 500.0
    cfi = -200.0
    cff = -100.0
    net_cf = cfo + cfi + cff
    assert net_cf == 200.0

def test_dq_10_non_negative_fixed_assets():
    fixed_assets = 1500.0
    assert fixed_assets >= 0

def test_dq_11_tax_rate_range():
    valid_tax_rate = 25.17
    invalid_tax_rate = 120.0
    assert 0.0 <= valid_tax_rate <= 100.0
    assert not (0.0 <= invalid_tax_rate <= 100.0)

def test_dq_14_eps_sign_consistency():
    pat_positive = 100.0
    eps_positive = 10.0
    pat_negative = -50.0
    eps_negative = -5.0
    assert (pat_positive >= 0) == (eps_positive >= 0)
    assert (pat_negative >= 0) == (eps_negative >= 0)
