"""
Sector Benchmark Report PDF Generator (Sprint 5 — Day 34).

Generates 11 publication-grade Sector Intelligence PDF reports.
Each Sector Report includes:
- Executive Sector Header (Sector Name, Constituent Count, Total Market Cap)
- Sector Summary KPI Tiles (Median ROE, ROCE, NPM, D/E, 5-Yr Revenue CAGR, Quality Score)
- Sector Multiples & Capital Return Summary Table
- Complete Constituent Comparative Matrix across 8 Core Fundamental Metrics
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.units import inch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
SECTOR_REPORT_DIR = PROJECT_ROOT / "reports" / "sector"

# Institutional Palette
NAVY_PRIMARY = colors.HexColor("#0A1628")
EMERALD_GREEN = colors.HexColor("#00D294")
GOLD_ACCENT = colors.HexColor("#F59E0B")
SLATE_BG = colors.HexColor("#F8FAFC")
SLATE_BORDER = colors.HexColor("#E2E8F0")
SLATE_TEXT = colors.HexColor("#475569")
DARK_TEXT = colors.HexColor("#0F172A")


def sanitize_filename(name: str) -> str:
    """Sanitize sector name for filesystem."""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name).strip("_")


def generate_single_sector_report(
    sector_name: str,
    output_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a sector benchmark PDF report for the specified sector or peer group.
    """
    SECTOR_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        clean_name = sanitize_filename(sector_name)
        output_path = SECTOR_REPORT_DIR / f"{clean_name}_report.pdf"

    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(str(DB_PATH))
    # Query companies matching either sector, peer group, or industry
    sec_query = """
        SELECT c.company_id, c.company_name, s.sector, s.industry, s.market_cap_category
        FROM companies c
        JOIN sectors s ON c.company_id = s.company_id
        WHERE s.sector = ?
        ORDER BY c.company_name ASC
    """
    sec_companies = pd.read_sql_query(sec_query, conn, params=(sector_name,))

    # If empty, check peer_percentiles or peer_groups
    if sec_companies.empty:
        peer_query = """
            SELECT DISTINCT c.company_id, c.company_name, s.sector, s.industry, s.market_cap_category
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.company_id
            LEFT JOIN sectors s ON c.company_id = s.company_id
            WHERE pp.peer_group_name = ?
            ORDER BY c.company_name ASC
        """
        sec_companies = pd.read_sql_query(peer_query, conn, params=(sector_name,))

    # If still empty, check raw peer_groups.xlsx
    if sec_companies.empty and (PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx").exists():
        try:
            pg_df = pd.read_excel(PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx")
            pg_matches = pg_df[pg_df["peer_group_name"] == sector_name]
            if not pg_matches.empty:
                cids = pg_matches["company_id"].tolist()
                placeholders = ",".join(["?"] * len(cids))
                sec_companies = pd.read_sql_query(
                    f"SELECT c.company_id, c.company_name, s.sector, s.industry, s.market_cap_category FROM companies c LEFT JOIN sectors s ON c.company_id = s.company_id WHERE c.company_id IN ({placeholders})",
                    conn, params=cids
                )
        except Exception:
            pass

    if sec_companies.empty:
        conn.close()
        return None

    cids = sec_companies["company_id"].tolist()
    placeholders = ",".join(["?"] * len(cids))

    # Fetch latest ratios
    ratios_query = f"""
        SELECT fr.*
        FROM financial_ratios fr
        WHERE fr.company_id IN ({placeholders})
          AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id IN ({placeholders}))
    """
    ratios_df = pd.read_sql_query(ratios_query, conn, params=cids + cids)

    # Fetch latest P&L
    pl_query = f"""
        SELECT pl.company_id, pl.sales, pl.net_profit
        FROM profitandloss pl
        WHERE pl.company_id IN ({placeholders})
          AND pl.year = (SELECT MAX(year) FROM profitandloss WHERE company_id IN ({placeholders}))
    """
    pl_df = pd.read_sql_query(pl_query, conn, params=cids + cids)
    conn.close()

    # Merge data
    merged = sec_companies.merge(ratios_df, on="company_id", how="left").merge(pl_df, on="company_id", how="left")

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SecTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#FFFFFF")
    )
    sub_style = ParagraphStyle(
        "SecSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#CBD5E1")
    )
    hdr_style = ParagraphStyle(
        "SecHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=NAVY_PRIMARY
    )
    tbl_hdr_style = ParagraphStyle(
        "TblHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=colors.HexColor("#FFFFFF")
    )
    tbl_cell_style = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=DARK_TEXT
    )
    tbl_cell_center = ParagraphStyle(
        "TblCellC",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        alignment=1,
        textColor=DARK_TEXT
    )
    tbl_cell_right = ParagraphStyle(
        "TblCellR",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        alignment=2,
        textColor=DARK_TEXT
    )

    story = []

    # 1. Header Banner
    num_comps = len(sec_companies)
    header_data = [
        [
            Paragraph(f"<b>SECTOR INTELLIGENCE REPORT: {sector_name.upper()}</b>", title_style),
            Paragraph(f"<b>Universe:</b> Nifty 100 Constituents | <b>Coverage:</b> {num_comps} Companies<br/><b>Benchmark Date:</b> FY2024 Final Audit | <b>Classification:</b> Institutional", sub_style)
        ]
    ]
    hdr_table = Table(header_data, colWidths=[6.0 * inch, 4.0 * inch])
    hdr_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 10))

    # 2. Sector Summary KPI Bento Tiles
    med_roe = merged["return_on_equity_pct"].median() if "return_on_equity_pct" in merged.columns else 0.0
    med_roce = merged["roce_pct"].median() if "roce_pct" in merged.columns else 0.0
    med_npm = merged["net_profit_margin_pct"].median() if "net_profit_margin_pct" in merged.columns else 0.0
    med_de = merged["debt_to_equity"].median() if "debt_to_equity" in merged.columns else 0.0
    med_rev_cagr = merged["revenue_cagr_5yr"].median() if "revenue_cagr_5yr" in merged.columns else 0.0
    med_quality = merged["composite_quality_score"].median() if "composite_quality_score" in merged.columns else 0.0

    kpi_tile_data = [
        [
            [Paragraph(f"{med_roe:.1f}%", ParagraphStyle("V1", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=EMERALD_GREEN)), Paragraph("MEDIAN ROE", ParagraphStyle("L1", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))],
            [Paragraph(f"{med_roce:.1f}%", ParagraphStyle("V2", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=GOLD_ACCENT)), Paragraph("MEDIAN ROCE", ParagraphStyle("L2", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))],
            [Paragraph(f"{med_npm:.1f}%", ParagraphStyle("V3", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=DARK_TEXT)), Paragraph("MEDIAN NPM", ParagraphStyle("L3", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))],
            [Paragraph(f"{med_de:.2f}", ParagraphStyle("V4", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=DARK_TEXT)), Paragraph("MEDIAN D/E", ParagraphStyle("L4", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))],
            [Paragraph(f"{med_rev_cagr:.1f}%", ParagraphStyle("V5", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=EMERALD_GREEN)), Paragraph("5-YR REV CAGR", ParagraphStyle("L5", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))],
            [Paragraph(f"{med_quality:.1f}", ParagraphStyle("V6", fontName="Helvetica-Bold", fontSize=13, alignment=1, textColor=GOLD_ACCENT)), Paragraph("QUALITY SCORE", ParagraphStyle("L6", fontName="Helvetica", fontSize=7, alignment=1, textColor=SLATE_TEXT))]
        ]
    ]
    tile_table = Table(kpi_tile_data, colWidths=[1.66 * inch] * 6, rowHeights=[38])
    tile_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, SLATE_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, SLATE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tile_table)
    story.append(Spacer(1, 12))

    # 3. Complete Constituent Benchmark Table (8 metrics)
    story.append(Paragraph(f"<b>Constituent Performance & Valuation Matrix ({num_comps} Companies)</b>", hdr_style))
    story.append(Spacer(1, 4))

    table_headers = [
        Paragraph("Ticker", tbl_hdr_style),
        Paragraph("Company Name", tbl_hdr_style),
        Paragraph("Industry", tbl_hdr_style),
        Paragraph("Sales (Cr)", tbl_hdr_style),
        Paragraph("Net Profit", tbl_hdr_style),
        Paragraph("ROE %", tbl_hdr_style),
        Paragraph("ROCE %", tbl_hdr_style),
        Paragraph("D/E", tbl_hdr_style),
        Paragraph("5Y CAGR", tbl_hdr_style),
        Paragraph("Quality", tbl_hdr_style)
    ]

    matrix_rows = [table_headers]

    for _, row in merged.iterrows():
        cid = row.get("company_id", "")
        cname = str(row.get("company_name", cid))[:26]
        ind = str(row.get("industry", ""))[:20]
        sales = f"Rs. {row.get('sales', 0):,.0f}" if pd.notna(row.get('sales')) else "N/A"
        pat = f"Rs. {row.get('net_profit', 0):,.0f}" if pd.notna(row.get('net_profit')) else "N/A"
        roe = f"{row.get('return_on_equity_pct', 0):.1f}%" if pd.notna(row.get('return_on_equity_pct')) else "N/A"
        roce = f"{row.get('roce_pct', 0):.1f}%" if pd.notna(row.get('roce_pct')) else "N/A"
        de = f"{row.get('debt_to_equity', 0):.2f}" if pd.notna(row.get('debt_to_equity')) else "0.00"
        cagr = f"{row.get('revenue_cagr_5yr', 0):.1f}%" if pd.notna(row.get('revenue_cagr_5yr')) else "N/A"
        q_score = f"{row.get('composite_quality_score', 0):.1f}" if pd.notna(row.get('composite_quality_score')) else "N/A"

        matrix_rows.append([
            Paragraph(f"<b>{cid}</b>", tbl_cell_center),
            Paragraph(cname, tbl_cell_style),
            Paragraph(ind, tbl_cell_style),
            Paragraph(sales, tbl_cell_right),
            Paragraph(pat, tbl_cell_right),
            Paragraph(roe, tbl_cell_right),
            Paragraph(roce, tbl_cell_right),
            Paragraph(de, tbl_cell_center),
            Paragraph(cagr, tbl_cell_right),
            Paragraph(q_score, tbl_cell_center)
        ])

    col_widths = [0.85*inch, 1.85*inch, 1.45*inch, 1.05*inch, 1.05*inch, 0.75*inch, 0.75*inch, 0.65*inch, 0.80*inch, 0.80*inch]
    matrix_table = Table(matrix_rows, colWidths=col_widths, repeatRows=1)
    matrix_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FFFFFF")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ("BOX", (0, 0), (-1, -1), 0.8, SLATE_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(matrix_table)

    # Footer
    story.append(Spacer(1, 12))
    footer_tbl = Table([
        [
            Paragraph("<font color='#64748B' size='7'>Bluestock Fintech Nifty 100 Intelligence Platform | Sector Research Suite</font>", styles["Normal"]),
            Paragraph(f"<font color='#64748B' size='7'>Sector: {sector_name} | Generated September 2026</font>", ParagraphStyle("RF", alignment=2))
        ]
    ], colWidths=[6.0 * inch, 4.0 * inch])
    story.append(footer_tbl)

    doc.build(story)
    return output_path


def batch_generate_all_sector_reports() -> Tuple[int, List[str]]:
    """
    Generate sector reports for all 11 peer group sectors and broad sectors.
    Returns (success_count, generated_names).
    """
    SECTOR_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    sectors_to_generate = []

    # 1. 11 Peer Group Sectors
    if (PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx").exists():
        pg_df = pd.read_excel(PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx")
        sectors_to_generate.extend(pg_df["peer_group_name"].dropna().unique().tolist())

    # 2. Broad sectors from DB
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        db_secs = pd.read_sql_query("SELECT DISTINCT sector FROM sectors WHERE sector IS NOT NULL", conn)["sector"].tolist()
        conn.close()
        for s in db_secs:
            if s not in sectors_to_generate:
                sectors_to_generate.append(s)

    success_cnt = 0
    generated_names = []

    for sec in sectors_to_generate:
        try:
            res = generate_single_sector_report(sec)
            if res and res.exists():
                success_cnt += 1
                generated_names.append(sec)
        except Exception as e:
            print(f"Error generating sector report for {sec}: {e}")

    return success_cnt, generated_names


if __name__ == "__main__":
    cnt, secs = batch_generate_all_sector_reports()
    print(f"Generated {cnt} sector reports for: {secs}")
