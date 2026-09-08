"""
Valuation Module & Multiple Analyzer (Sprint 4 — Day 26).
Computes:
- Free Cash Flow (FCF) Yield: FCF / Market Cap * 100
- Sector Median P/E for 11 broad sectors
- 5-Year Historical Median P/E per company
- Overvaluation / Discount Classification:
  * Caution: P/E > Sector Median * 1.5
  * Discount: P/E < Sector Median * 0.7
  * Fair: Otherwise
Generates:
- output/valuation_summary.xlsx (all 92 companies)
- output/valuation_flags.csv (Caution & Discount companies only)
"""

import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "raw" / "market_cap.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"


def compute_fcf_yield(fcf_cr: Optional[float], market_cap_cr: Optional[float]) -> Optional[float]:
    """
    Compute FCF Yield (%).
    FCF Yield = (Free Cash Flow / Market Cap) * 100
    """
    if fcf_cr is None or market_cap_cr is None or market_cap_cr <= 0:
        return None
    return (fcf_cr / market_cap_cr) * 100.0


def classify_valuation_flag(pe_ratio: Optional[float], sector_median_pe: Optional[float]) -> str:
    """
    Classify valuation flag based on sector median comparison:
    - Caution: P/E > sector_median * 1.5 (Overvalued)
    - Discount: P/E < sector_median * 0.7 (Undervalued)
    - Fair: Otherwise
    """
    if pe_ratio is None or pd.isna(pe_ratio) or sector_median_pe is None or pd.isna(sector_median_pe) or sector_median_pe <= 0:
        return "Fair"
    if pe_ratio > (sector_median_pe * 1.5):
        return "Caution"
    elif pe_ratio < (sector_median_pe * 0.7):
        return "Discount"
    return "Fair"


def run_valuation_analysis(
    target_year: int = 2024,
    db_path: Path = DB_PATH,
    market_cap_path: Path = MARKET_CAP_PATH
) -> pd.DataFrame:
    """
    Execute end-to-end valuation analysis across all 92 companies:
    Merges market_cap.xlsx valuation metrics with SQLite financial_ratios, companies, and sectors.
    Computes FCF yield, sector median P/E, 5-year historical median P/E, and valuation flags.
    """
    conn = sqlite3.connect(str(db_path))
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    comp_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT company_id, sector, industry FROM sectors", conn)
    conn.close()

    mc_df = pd.read_excel(market_cap_path)

    # Calculate 5-year historical median P/E per company
    pe_5yr_median_map = {}
    for cid, c_mc in mc_df.groupby("company_id"):
        # Consider available recent years up to target_year
        valid_pe = c_mc[(c_mc["year"] <= target_year) & (c_mc["pe_ratio"] > 0)]["pe_ratio"].dropna()
        pe_5yr_median_map[cid] = float(valid_pe.median()) if not valid_pe.empty else None

    # Filter to target_year
    mc_latest = mc_df[mc_df["year"] == target_year].copy()
    ratios_latest = ratios_df[ratios_df["year"] == target_year].copy()

    # Merge data
    val_df = comp_df.merge(sec_df, on="company_id", how="left")
    val_df = val_df.merge(
        mc_latest[["company_id", "market_cap_crore", "enterprise_value_crore", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"]],
        on="company_id",
        how="left"
    )
    val_df = val_df.merge(
        ratios_latest[["company_id", "free_cash_flow_cr", "return_on_equity_pct", "debt_to_equity"]],
        on="company_id",
        how="left"
    )

    # 1. Compute FCF Yield
    val_df["fcf_yield_pct"] = val_df.apply(
        lambda r: compute_fcf_yield(r["free_cash_flow_cr"], r["market_cap_crore"]),
        axis=1
    )

    # 2. Compute Sector Median P/E for latest year
    # Only consider positive P/E for sector median calculation
    valid_pe_df = val_df[val_df["pe_ratio"] > 0]
    sector_pe_medians = valid_pe_df.groupby("sector")["pe_ratio"].median().to_dict()
    val_df["sector_median_pe"] = val_df["sector"].map(sector_pe_medians)

    # Universe median fallback if sector median missing
    universe_pe_median = float(valid_pe_df["pe_ratio"].median())
    val_df["sector_median_pe"] = val_df["sector_median_pe"].fillna(universe_pe_median)

    # 3. 5-Year Historical Median P/E
    val_df["pe_5yr_median"] = val_df["company_id"].map(pe_5yr_median_map)

    # 4. P/E vs Sector Median %
    val_df["pe_vs_sector_median_pct"] = (
        (val_df["pe_ratio"] - val_df["sector_median_pe"]) / val_df["sector_median_pe"] * 100.0
    ).round(2)

    # 5. Overvaluation Flag
    val_df["valuation_flag"] = val_df.apply(
        lambda r: classify_valuation_flag(r["pe_ratio"], r["sector_median_pe"]),
        axis=1
    )

    return val_df


def generate_valuation_reports(output_dir: Path = OUTPUT_DIR) -> Tuple[Path, Path]:
    """
    Generate:
    1. output/valuation_summary.xlsx (92 companies formatted with OpenPyXL)
    2. output/valuation_flags.csv (Caution & Discount flagged companies)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    val_df = run_valuation_analysis()

    # Define export columns
    export_cols = [
        "company_id", "company_name", "sector",
        "pe_ratio", "pb_ratio", "ev_ebitda",
        "fcf_yield_pct", "pe_5yr_median",
        "pe_vs_sector_median_pct", "valuation_flag"
    ]

    clean_df = val_df[export_cols].copy()

    # 1. Generate Excel Summary with formatting
    xlsx_path = output_dir / "valuation_summary.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Valuation Summary"

    # Styling definitions
    header_fill = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
    caution_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Light Red
    discount_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid") # Light Green
    fair_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")     # Neutral Gray
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
    normal_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    # Write Headers
    for col_idx, col_name in enumerate(export_cols, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.value = col_name.replace("_", " ").title()
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = 18 if "name" in col_name or "sector" in col_name else 14

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "C2"

    # Write Data Rows
    for row_idx, (_, row) in enumerate(clean_df.iterrows(), start=2):
        flag = row["valuation_flag"]
        for col_idx, col_name in enumerate(export_cols, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            val = row[col_name]
            cell.value = round(float(val), 2) if isinstance(val, float) and pd.notna(val) else val
            cell.font = normal_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")

            # Color-code Flag column
            if col_name == "valuation_flag":
                if flag == "Caution":
                    cell.fill = caution_fill
                elif flag == "Discount":
                    cell.fill = discount_fill
                else:
                    cell.fill = fair_fill

    wb.save(str(xlsx_path))
    print(f"Saved: {xlsx_path}")

    # 2. Generate CSV for Caution / Discount companies
    csv_path = output_dir / "valuation_flags.csv"
    flagged_df = clean_df[clean_df["valuation_flag"].isin(["Caution", "Discount"])].copy()
    flagged_df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path} (Flagged count: {len(flagged_df)})")

    return xlsx_path, csv_path


if __name__ == "__main__":
    generate_valuation_reports()
