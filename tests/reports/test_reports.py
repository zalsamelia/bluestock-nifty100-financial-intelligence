"""
Unit Tests for ReportLab PDF Reporting Suite (Sprint 5 — Days 33, 34, 35).
"""

import pytest
from pathlib import Path

from src.reports.tearsheet import generate_company_tearsheet
from src.reports.sector_report import generate_single_sector_report
from src.reports.portfolio_summary import generate_portfolio_summary_pdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"
SECTOR_DIR = PROJECT_ROOT / "reports" / "sector"
PORTFOLIO_DIR = PROJECT_ROOT / "reports" / "portfolio"


def test_generate_single_tearsheet():
    """Verify single company tearsheet generation produces valid non-empty PDF >= 30KB."""
    pdf_path = generate_company_tearsheet("TCS")
    assert pdf_path is not None
    assert Path(pdf_path).exists()
    size_bytes = Path(pdf_path).stat().st_size
    assert size_bytes >= 30000, f"Tearsheet size {size_bytes} bytes is less than 30KB"


def test_generate_single_sector_report():
    """Verify sector benchmark report generation."""
    pdf_path = generate_single_sector_report("Financials")
    assert pdf_path is not None
    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 5000


def test_generate_portfolio_summary_pdf():
    """Verify portfolio summary PDF generation."""
    pdf_path = generate_portfolio_summary_pdf()
    assert pdf_path is not None
    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 10000
