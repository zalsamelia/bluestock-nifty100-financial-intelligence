"""
Screener Excel Output Generator (Sprint 3 — Day 17).
Generates output/screener_output.xlsx with 6 sheets — one per preset screener
plus an 'All Companies' overview sheet.
Each sheet contains 20+ KPI columns sorted by composite_quality_score descending.
Cell fills: green for threshold-passing metrics, red for threshold-failing.
Uses openpyxl for formatting.
"""

import os
import sys
import sqlite3
import warnings
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.screener.engine import run_screener, load_screener_config, load_full_screener_dataset
OUTPUT_DIR = PROJECT_ROOT / "output"

# Columns to display in screener Excel output
OUTPUT_COLUMNS = [
    "company_id", "company_name", "sector", "industry", "market_cap_category",
    "composite_quality_score",
    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "return_on_assets_pct",
    "debt_to_equity", "interest_coverage", "icr_label", "net_debt_cr",
    "free_cash_flow_cr", "cfo_quality_score", "cfo_quality_label", "fcf_conversion_pct",
    "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
    "pe_ratio", "pb_ratio", "dividend_yield_pct", "market_cap_crore",
    "capital_allocation_pattern", "book_value_per_share",
]

# Threshold configurations for cell fill formatting
THRESHOLD_CONFIG = {
    "return_on_equity_pct":   {"min": 15.0,  "max": None},
    "roce_pct":               {"min": 12.0,  "max": None},
    "net_profit_margin_pct":  {"min": 8.0,   "max": None},
    "debt_to_equity":         {"min": None,  "max": 2.0},
    "interest_coverage":      {"min": 3.0,   "max": None},
    "free_cash_flow_cr":      {"min": 0.0,   "max": None},
    "cfo_quality_score":      {"min": 0.7,   "max": None},
    "revenue_cagr_5yr":       {"min": 10.0,  "max": None},
    "pat_cagr_5yr":           {"min": 10.0,  "max": None},
    "eps_cagr_5yr":           {"min": 10.0,  "max": None},
    "pe_ratio":               {"min": None,  "max": 40.0},
    "pb_ratio":               {"min": None,  "max": 5.0},
    "dividend_yield_pct":     {"min": 0.5,   "max": None},
    "composite_quality_score":{"min": 60.0,  "max": None},
}

# Colors
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
RED_FILL   = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
ALT_ROW_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
NORMAL_FONT = Font(name="Calibri", size=10)


def _apply_sheet_formatting(ws, df: pd.DataFrame, colored_cols: list) -> None:
    """Apply header formatting, column widths, and conditional cell fills to worksheet."""
    # Column width mapping
    col_widths = {
        "company_id": 14, "company_name": 28, "sector": 18, "industry": 22,
        "market_cap_category": 16, "composite_quality_score": 20,
        "icr_label": 14, "cfo_quality_label": 18, "capital_allocation_pattern": 22,
    }
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    # Header row
    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = col_name.replace("_", " ").title()
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

        # Set column width
        default_width = col_widths.get(col_name, 14)
        ws.column_dimensions[get_column_letter(col_idx)].width = default_width

    # Data rows
    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        is_alt = (row_idx % 2 == 0)
        for col_idx, col_name in enumerate(df.columns, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = row[col_name]
            cell.font = NORMAL_FONT
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")

            # Conditional fill for metric columns
            if col_name in colored_cols and col_name in THRESHOLD_CONFIG:
                cfg = THRESHOLD_CONFIG[col_name]
                val = row[col_name]
                if pd.notna(val):
                    passes = True
                    if cfg.get("min") is not None and val < cfg["min"]:
                        passes = False
                    if cfg.get("max") is not None and val > cfg["max"]:
                        passes = False
                    cell.fill = GREEN_FILL if passes else RED_FILL
                elif is_alt:
                    cell.fill = ALT_ROW_FILL
            elif is_alt:
                cell.fill = ALT_ROW_FILL

    # Freeze first row
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 30


def _round_df(df: pd.DataFrame) -> pd.DataFrame:
    """Round float columns to 2 decimal places for clean Excel display."""
    for col in df.select_dtypes(include=[float]).columns:
        df[col] = df[col].round(2)
    return df


def generate_screener_excel(
    output_path: Optional[Path] = None,
    target_year: int = 2024
) -> Path:
    """
    Generate output/screener_output.xlsx with exactly 6 preset sheets.
    Each sheet: 20+ KPI columns, sorted by composite_quality_score desc, green/red fills.
    """
    output_path = output_path or (OUTPUT_DIR / "screener_output.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_screener_config()
    preset_keys = list(config["presets"].keys())

    wb = Workbook()
    wb.remove(wb.active)   # Remove default blank sheet

    # Generate 6 preset sheets
    for preset_key in preset_keys:
        preset_label = config["presets"][preset_key]["name"]
        sheet_title = preset_label[:31]  # Excel limits to 31 chars
        ws = wb.create_sheet(title=sheet_title)

        preset_df = run_screener(preset_name=preset_key, target_year=target_year)
        avail = [c for c in OUTPUT_COLUMNS if c in preset_df.columns]
        colored = [c for c in avail if c in THRESHOLD_CONFIG]
        out = _round_df(preset_df[avail].copy())
        _apply_sheet_formatting(ws, out, colored)

        # Add total count note below last data row
        last_row = len(out) + 2
        ws.cell(row=last_row, column=1).value = f"Total companies matching filter: {len(out)}"
        ws.cell(row=last_row, column=1).font = Font(bold=True, size=10, color="1F3864")

        # Add a note at top row A1 showing company count
        # (cell A1 contains header already; add count below last data row)
        last_row = len(out) + 2
        ws.cell(row=last_row, column=1).value = f"Total companies matching filter: {len(out)}"
        ws.cell(row=last_row, column=1).font = Font(bold=True, size=10, color="1F3864")

    wb.save(str(output_path))
    print(f"Saved screener_output.xlsx: {output_path}")
    return output_path
