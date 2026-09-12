"""
Unit Tests for Automated Pros & Cons Generator (Sprint 5 — Day 30).
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.nlp.pros_cons_generator import generate_all_pros_cons, evaluate_company_pros_cons

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
PROS_CONS_CSV = OUTPUT_DIR / "pros_cons_generated.csv"


def test_generate_all_pros_cons_coverage():
    """Verify that every company has at least 1 pro and at least 1 con with confidence > 60%."""
    df = generate_all_pros_cons()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert PROS_CONS_CSV.exists()

    required_cols = ["company_id", "type", "rule_id", "text", "confidence_pct"]
    for col in required_cols:
        assert col in df.columns

    # Check confidence threshold
    assert (df["confidence_pct"] > 60.0).all()

    # Verify every company in companies table has >= 1 pro and >= 1 con
    conn = sqlite3.connect(str(DB_PATH))
    companies = pd.read_sql_query("SELECT company_id FROM companies", conn)["company_id"].tolist()
    conn.close()

    for cid in companies:
        c_df = df[df["company_id"] == cid]
        assert not c_df.empty, f"Company {cid} has no pros/cons generated"
        pros = c_df[c_df["type"] == "pro"]
        cons = c_df[c_df["type"] == "con"]
        assert len(pros) >= 1, f"Company {cid} has 0 pros"
        assert len(cons) >= 1, f"Company {cid} has 0 cons"


def test_evaluate_company_pros_cons_rules():
    """Test evaluation on synthetic test dataframe."""
    ratios = pd.DataFrame([{
        "year": 2024,
        "return_on_equity_pct": 25.0,
        "debt_to_equity": 0.0,
        "revenue_cagr_5yr": 18.0,
        "pat_cagr_5yr": 22.0,
        "operating_profit_margin_pct": 28.0,
        "interest_coverage_ratio": 50.0,
        "free_cash_flow_cr": 5000.0,
        "dividend_yield_pct": 2.5
    }])
    pl = pd.DataFrame([{
        "year": 2024,
        "sales": 100000.0,
        "net_profit": 20000.0,
        "operating_profit": 30000.0
    }])
    bs = pd.DataFrame([{
        "year": 2024,
        "total_assets": 150000.0,
        "borrowings": 0.0
    }])
    cf = pd.DataFrame([{
        "year": 2024,
        "operating_activity": 15000.0,
        "investing_activity": -5000.0,
        "financing_activity": -2000.0
    }])

    res = evaluate_company_pros_cons("TESTCO", ratios, pl, bs, cf, sector="Information Technology")
    pro_rule_ids = [r["rule_id"] for r in res if r["type"] == "pro"]
    assert "PRO_03" in pro_rule_ids  # Debt Free
    assert "PRO_04" in pro_rule_ids  # Rev CAGR > 15%
    assert "PRO_05" in pro_rule_ids  # OPM > 25%
