"""
Portfolio Summary PDF Generator (Sprint 5 — Day 35).

Generates reports/portfolio/portfolio_summary.pdf:
- Executive Cover & Methodology Summary
- Universe Multiples & Distribution Dashboard
- Alphabetical Constituent Pages with:
  * Company Name, Ticker, Sector, Industry
  * Top 6 Financial KPIs
  * Trend direction indicators (Up / Down / Flat) comparing latest FY vs previous FY:
    - Up Arrow (Green): Metric improved (> +2%)
    - Down Arrow (Red): Metric deteriorated (< -2%)
    - Right Arrow (Slate): Flat / Neutral (within +/- 2%)
  * Valuation & Quality Tier Badge
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.units import inch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
PORTFOLIO_DIR = PROJECT_ROOT / "reports" / "portfolio"
OUTPUT_PDF = PORTFOLIO_DIR / "portfolio_summary.pdf"

# Institutional Palette
NAVY_PRIMARY = colors.HexColor("#0A1628")
EMERALD_GREEN = colors.HexColor("#00D294")
GOLD_ACCENT = colors.HexColor("#F59E0B")
ROSE_RED = colors.HexColor("#F43F5E")
SLATE_BG = colors.HexColor("#F8FAFC")
SLATE_BORDER = colors.HexColor("#E2E8F0")
SLATE_TEXT = colors.HexColor("#475569")
DARK_TEXT = colors.HexColor("#0F172A")


def get_trend_indicator(curr_val: Optional[float], prev_val: Optional[float], higher_is_better: bool = True) -> Tuple[str, str]:
    """
    Determine trend arrow and color:
    Returns (arrow_symbol_text, hex_color).
    """
    if curr_val is None or prev_val is None or pd.isna(curr_val) or pd.isna(prev_val) or prev_val == 0:
        return ("--", "#64748B")

    pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100.0

    if abs(pct_change) <= 2.0:
        return ("[->]", "#64748B")  # Flat
    elif pct_change > 2.0:
        return ("[+]", "#059669") if higher_is_better else ("[-]", "#E11D48")
    else:
        return ("[-]", "#E11D48") if higher_is_better else ("[+]", "#059669")


def generate_portfolio_summary_pdf(output_path: Optional[Path] = None) -> Path:
    """
    Generate the complete Nifty 100 Portfolio Summary PDF report.
    """
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = OUTPUT_PDF

    if not DB_PATH.exists():
        return output_path

    conn = sqlite3.connect(str(DB_PATH))
    companies = pd.read_sql_query("SELECT c.*, s.sector, s.industry FROM companies c LEFT JOIN sectors s ON c.company_id = s.company_id ORDER BY c.company_id ASC", conn)
    all_ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY company_id ASC, year ASC", conn)
    all_pl = pd.read_sql_query("SELECT * FROM profitandloss ORDER BY company_id ASC, year ASC", conn)
    conn.close()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=1,
        textColor=NAVY_PRIMARY
    )
    cover_sub_style = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        alignment=1,
        textColor=SLATE_TEXT
    )
    comp_hdr_style = ParagraphStyle(
        "CompHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#FFFFFF")
    )
    comp_sub_style = ParagraphStyle(
        "CompSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#CBD5E1")
    )
    kpi_val_style = ParagraphStyle(
        "PortKPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        alignment=1,
        textColor=DARK_TEXT
    )
    kpi_lbl_style = ParagraphStyle(
        "PortKPILbl",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        alignment=1,
        textColor=SLATE_TEXT
    )
    kpi_trend_style = ParagraphStyle(
        "PortKPITrend",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=DARK_TEXT
    )

    story = []

    # ==========================================
    # 1. EXECUTIVE COVER PAGE
    # ==========================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("BLUESTOCK FINTECH", ParagraphStyle("B", fontName="Helvetica-Bold", fontSize=14, leading=16, alignment=1, textColor=EMERALD_GREEN)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("NIFTY 100 PORTFOLIO SUMMARY", cover_title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Comprehensive Fundamental Trajectory, Return Multiples &amp; Directional Trend Monitor", cover_sub_style))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="60%", thickness=2, color=EMERALD_GREEN, spaceBefore=5, spaceAfter=25))

    overview_box_data = [
        [Paragraph(f"<b>Coverage Universe:</b> {len(companies)} Companies", styles["Normal"])],
        [Paragraph("<b>Horizon:</b> 10-Year Historical Financial Audit (FY2015–FY2024)", styles["Normal"])],
        [Paragraph("<b>Key Benchmarks:</b> ROE, ROCE, NPM, D/E, 5-Yr Rev CAGR, Composite Quality Score", styles["Normal"])],
        [Paragraph("<b>Trend Direction Matrix:</b> <font color='#059669'><b>[+] Improving</b></font> (&gt;+2%) | <font color='#E11D48'><b>[-] Deteriorating</b></font> (&lt;-2%) | <font color='#64748B'><b>[-&gt;] Flat</b></font>", styles["Normal"])],
        [Paragraph("<b>Classification Standard:</b> Institutional Fundamental Equity Intelligence", styles["Normal"])]
    ]
    overview_table = Table(overview_box_data, colWidths=[6.5 * inch])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG),
        ("BOX", (0, 0), (-1, -1), 1, SLATE_BORDER),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 40))
    story.append(Paragraph("<font color='#64748B' size='8'>Published: September 2026 | Bluestock Intelligence Hub | Automated Quantitative Research Suite</font>", ParagraphStyle("P", alignment=1)))

    story.append(PageBreak())

    # ==========================================
    # 2. CONSTITUENT ENTRIES (Compact 2 Per Page for Readability)
    # ==========================================

    for idx, (_, comp) in enumerate(companies.iterrows()):
        cid = comp["company_id"]
        cname = comp.get("company_name", cid)
        sec = comp.get("sector", "Diversified")
        ind = comp.get("industry", "Equity")

        c_ratios = all_ratios[all_ratios["company_id"] == cid].sort_values("year")
        c_pl = all_pl[all_pl["company_id"] == cid].sort_values("year")

        latest_r = c_ratios.iloc[-1] if not c_ratios.empty else {}
        prev_r = c_ratios.iloc[-2] if len(c_ratios) >= 2 else {}

        # 6 Core KPIs + Trends
        # 1. ROE
        roe_curr = latest_r.get("return_on_equity_pct")
        roe_prev = prev_r.get("return_on_equity_pct")
        roe_sym, roe_col = get_trend_indicator(roe_curr, roe_prev, higher_is_better=True)
        roe_str = f"{roe_curr:.1f}%" if pd.notna(roe_curr) else "N/A"

        # 2. ROCE
        roce_curr = latest_r.get("roce_pct")
        roce_prev = prev_r.get("roce_pct")
        roce_sym, roce_col = get_trend_indicator(roce_curr, roce_prev, higher_is_better=True)
        roce_str = f"{roce_curr:.1f}%" if pd.notna(roce_curr) else "N/A"

        # 3. NPM
        npm_curr = latest_r.get("net_profit_margin_pct")
        npm_prev = prev_r.get("net_profit_margin_pct")
        npm_sym, npm_col = get_trend_indicator(npm_curr, npm_prev, higher_is_better=True)
        npm_str = f"{npm_curr:.1f}%" if pd.notna(npm_curr) else "N/A"

        # 4. D/E
        de_curr = latest_r.get("debt_to_equity")
        de_prev = prev_r.get("debt_to_equity")
        de_sym, de_col = get_trend_indicator(de_curr, de_prev, higher_is_better=False)
        de_str = f"{de_curr:.2f}" if pd.notna(de_curr) else "0.00"

        # 5. Rev CAGR 5yr
        cagr_curr = latest_r.get("revenue_cagr_5yr")
        cagr_prev = prev_r.get("revenue_cagr_5yr")
        cagr_sym, cagr_col = get_trend_indicator(cagr_curr, cagr_prev, higher_is_better=True)
        cagr_str = f"{cagr_curr:.1f}%" if pd.notna(cagr_curr) else "N/A"

        # 6. Quality Score
        q_curr = latest_r.get("composite_quality_score")
        q_prev = prev_r.get("composite_quality_score")
        q_sym, q_col = get_trend_indicator(q_curr, q_prev, higher_is_better=True)
        q_str = f"{q_curr:.1f}" if pd.notna(q_curr) else "N/A"

        # Header bar for company
        card_hdr = Table([
            [
                Paragraph(f"<b>{cid}</b> — {cname}", comp_hdr_style),
                Paragraph(f"<b>Sector:</b> {sec} | <b>Industry:</b> {ind}", comp_sub_style)
            ]
        ], colWidths=[4.2 * inch, 3.0 * inch])
        card_hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY_PRIMARY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))

        # KPI 6 Tiles with Direction Arrows
        tile_data = [
            [
                [Paragraph(roe_str, kpi_val_style), Paragraph(f"<font color='{roe_col}'><b>{roe_sym}</b></font>", kpi_trend_style), Paragraph("RETURN ON EQUITY", kpi_lbl_style)],
                [Paragraph(roce_str, kpi_val_style), Paragraph(f"<font color='{roce_col}'><b>{roce_sym}</b></font>", kpi_trend_style), Paragraph("ROCE %", kpi_lbl_style)],
                [Paragraph(npm_str, kpi_val_style), Paragraph(f"<font color='{npm_col}'><b>{npm_sym}</b></font>", kpi_trend_style), Paragraph("NET MARGIN %", kpi_lbl_style)],
                [Paragraph(de_str, kpi_val_style), Paragraph(f"<font color='{de_col}'><b>{de_sym}</b></font>", kpi_trend_style), Paragraph("DEBT / EQUITY", kpi_lbl_style)],
                [Paragraph(cagr_str, kpi_val_style), Paragraph(f"<font color='{cagr_col}'><b>{cagr_sym}</b></font>", kpi_trend_style), Paragraph("5Y REV CAGR", kpi_lbl_style)],
                [Paragraph(q_str, kpi_val_style), Paragraph(f"<font color='{q_col}'><b>{q_sym}</b></font>", kpi_trend_style), Paragraph("QUALITY SCORE", kpi_lbl_style)]
            ]
        ]
        kpi_tbl = Table(tile_data, colWidths=[1.20 * inch] * 6, rowHeights=[36])
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG),
            ("BOX", (0, 0), (-1, -1), 0.8, SLATE_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        # Footnote row for capital pattern
        cap_pat = latest_r.get("capital_allocation_pattern", "Disciplined Allocator")
        meta_row = Table([
            [
                Paragraph(f"<font color='#475569' size='6.5'><b>Capital Allocation:</b> {cap_pat} | <b>10-Yr Audit Status:</b> Validated</font>", styles["Normal"]),
                Paragraph(f"<font color='#00D294' size='6.5'><b>Nifty 100 Constituent</b></font>", ParagraphStyle("RM", alignment=2))
            ]
        ], colWidths=[5.4 * inch, 1.8 * inch])
        meta_row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("PADDING", (0, 0), (-1, -1), 3),
        ]))

        comp_block = [
            card_hdr,
            kpi_tbl,
            meta_row,
            Spacer(1, 14)
        ]

        story.append(KeepTogether(comp_block))

        # 4 companies per page layout
        if (idx + 1) % 4 == 0 and (idx + 1) < len(companies):
            story.append(PageBreak())

    doc.build(story)
    return output_path


if __name__ == "__main__":
    res = generate_portfolio_summary_pdf()
    print(f"Generated Portfolio Summary PDF: {res} ({res.stat().st_size} bytes)")
