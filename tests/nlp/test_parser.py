"""
Unit Tests for NLP Analysis Text Parser (Sprint 5 — Day 29).
"""

import pytest
import pandas as pd
from pathlib import Path

from src.nlp.parser import parse_text_cagr, parse_analysis_file, cross_validate_cagr

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def test_parse_text_cagr_standard():
    """Test regex extraction on standard strings."""
    text1 = "10 Years: 21%"
    res1 = parse_text_cagr(text1)
    assert len(res1) == 1
    assert res1[0] == (10, 21.0)

    text2 = "5 Years 14%"
    res2 = parse_text_cagr(text2)
    assert len(res2) == 1
    assert res2[0] == (5, 14.0)

    text3 = "3 Years: 13.5%"
    res3 = parse_text_cagr(text3)
    assert len(res3) == 1
    assert res3[0] == (3, 13.5)


def test_parse_text_cagr_multiple_matches():
    """Test string with multiple periods."""
    text = "10 Years: 15% | 5 Years: 18% | 3 Years: 22%"
    res = parse_text_cagr(text)
    assert len(res) == 3
    assert res[0] == (10, 15.0)
    assert res[1] == (5, 18.0)
    assert res[2] == (3, 22.0)


def test_parse_text_cagr_invalid():
    """Test non-matching and empty strings."""
    assert parse_text_cagr("") == []
    assert parse_text_cagr(None) == []
    assert parse_text_cagr("No data available") == []


def test_parse_analysis_file_outputs():
    """Test parsing analysis file and generating required CSV outputs."""
    parsed_df, failures_df = parse_analysis_file()
    assert isinstance(parsed_df, pd.DataFrame)
    assert isinstance(failures_df, pd.DataFrame)
    assert (OUTPUT_DIR / "analysis_parsed.csv").exists()
    assert (OUTPUT_DIR / "parse_failures.csv").exists()

    if not parsed_df.empty:
        assert "company_id" in parsed_df.columns
        assert "metric_type" in parsed_df.columns
        assert "period_years" in parsed_df.columns
        assert "value_pct" in parsed_df.columns


def test_cross_validate_cagr():
    """Test cross-validation of parsed values against calculated ratios."""
    parsed_df, _ = parse_analysis_file()
    if not parsed_df.empty:
        div_df = cross_validate_cagr(parsed_df)
        assert isinstance(div_df, pd.DataFrame)
