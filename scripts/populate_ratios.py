"""
Sprint 2 — Day 12: Populate financial_ratios Table.
Runs the full ratio engine for all 92 companies across all available years.
Writes all computed KPI columns into the financial_ratios table in SQLite.
Also exports output/capital_allocation.csv.
Also generates output/ratio_edge_cases.log (OPM cross-check anomalies).
Also generates output/sector_roce_notes.csv (Financials ROCE benchmarking).

Source tables (READ-ONLY): companies, profitandloss, balancesheet, cashflow, sectors.
Target table (WRITE): financial_ratios.
"""

import sqlite3
import logging
import csv
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_opm,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
    calculate_book_value_per_share,
)
from src.analytics.cagr import calculate_series_cagr
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
)
from src.analytics.quality_score import compute_percentile_scores

import pandas as pd

DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_PATH = OUTPUT_DIR / "ratio_edge_cases.log"
CAPITAL_ALLOC_PATH = OUTPUT_DIR / "capital_allocation.csv"
SECTOR_ROCE_NOTES_PATH = OUTPUT_DIR / "sector_roce_notes.csv"

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_PATH), mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def migrate_financial_ratios_table(conn: sqlite3.Connection) -> None:
    """
    Drop old financial_ratios table (placeholder ratio_1..ratio_13 schema)
    and recreate it with proper KPI column definitions.
    Source Sprint 1 tables are never touched.
    """
    cursor = conn.cursor()
    logger.info("Migrating financial_ratios table schema...")

    # Check existing schema
    existing_cols = [r[1] for r in cursor.execute("PRAGMA table_info(financial_ratios)").fetchall()]
    if "net_profit_margin_pct" not in existing_cols:
        logger.info("Old schema detected — dropping and recreating financial_ratios table.")
        cursor.execute("DROP TABLE IF EXISTS financial_ratios")
        cursor.execute("""
            CREATE TABLE financial_ratios (
                company_id TEXT NOT NULL,
                year INTEGER NOT NULL,

                net_profit_margin_pct REAL,
                operating_profit_margin_pct REAL,
                return_on_equity_pct REAL,
                roce_pct REAL,
                return_on_assets_pct REAL,
                debt_to_equity REAL,
                high_leverage_flag INTEGER,
                interest_coverage REAL,
                icr_label TEXT,
                icr_warning_flag INTEGER,
                net_debt_cr REAL,
                asset_turnover REAL,
                free_cash_flow_cr REAL,
                cfo_quality_score REAL,
                cfo_quality_label TEXT,
                capex_cr REAL,
                capex_intensity_pct REAL,
                capex_intensity_label TEXT,
                fcf_conversion_pct REAL,
                capital_allocation_pattern TEXT,
                earnings_per_share REAL,
                book_value_per_share REAL,
                dividend_payout_ratio_pct REAL,
                total_debt_cr REAL,
                cash_from_operations_cr REAL,
                revenue_cagr_3yr REAL,
                revenue_cagr_5yr REAL,
                revenue_cagr_10yr REAL,
                revenue_cagr_5yr_flag TEXT,
                pat_cagr_3yr REAL,
                pat_cagr_5yr REAL,
                pat_cagr_10yr REAL,
                pat_cagr_5yr_flag TEXT,
                eps_cagr_3yr REAL,
                eps_cagr_5yr REAL,
                eps_cagr_10yr REAL,
                eps_cagr_5yr_flag TEXT,
                composite_quality_score REAL,

                PRIMARY KEY (company_id, year),
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_financial_ratios_company
                ON financial_ratios(company_id)
        """)
        conn.commit()
        logger.info("financial_ratios table created with KPI schema.")
    else:
        logger.info("financial_ratios already has KPI schema. Clearing rows for fresh population.")
        cursor.execute("DELETE FROM financial_ratios")
        conn.commit()


def load_financials_sector_set(conn: sqlite3.Connection) -> set:
    """Return the set of company_ids in the Financials broad_sector."""
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT company_id FROM sectors WHERE sector = 'Financials'"
    ).fetchall()
    return {r["company_id"] for r in rows}


def load_profitandloss(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM profitandloss ORDER BY company_id, year", conn)


def load_balancesheet(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM balancesheet ORDER BY company_id, year", conn)


def load_cashflow(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM cashflow ORDER BY company_id, year", conn)


def load_companies(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM companies", conn)


def build_year_map(series: pd.Series, year_series: pd.Series) -> Dict[int, float]:
    """Build dict of {year: value} filtering out None/NaN."""
    result = {}
    for year, val in zip(year_series, series):
        if pd.notna(val) and val is not None:
            result[int(year)] = float(val)
    return result


def safe_float(val) -> Optional[float]:
    """Convert a value to float, returning None if conversion fails."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def compute_cfo_pat_ratios(cfo_series: pd.Series, pat_series: pd.Series, years: pd.Series, target_year: int, window: int = 5) -> List[float]:
    """Compute CFO/PAT ratios over a rolling window up to target_year."""
    ratios = []
    paired = [(int(y), safe_float(c), safe_float(p)) for y, c, p in zip(years, cfo_series, pat_series)]
    paired = sorted([x for x in paired if x[1] is not None and x[2] is not None and x[2] != 0], key=lambda x: x[0])
    recent = [x for x in paired if x[0] <= target_year][-window:]
    for _, cfo_val, pat_val in recent:
        ratios.append(cfo_val / pat_val)
    return ratios


def run_ratio_engine() -> None:
    """Main function to compute all KPIs and populate financial_ratios table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=" * 60)
    logger.info("Sprint 2 — Ratio Engine Starting")
    logger.info("=" * 60)

    conn = get_connection()

    # Step 1: Migrate schema
    migrate_financial_ratios_table(conn)

    # Step 2: Load source data (read-only)
    financials_companies = load_financials_sector_set(conn)
    pnl_df = load_profitandloss(conn)
    bs_df = load_balancesheet(conn)
    cf_df = load_cashflow(conn)
    companies_df = load_companies(conn)

    logger.info(f"Loaded {len(pnl_df)} P&L records, {len(bs_df)} BS records, {len(cf_df)} CF records.")
    logger.info(f"Financials sector companies: {len(financials_companies)}")

    # Step 3: Merge P&L + BS + CF
    merged = pnl_df.merge(bs_df, on=["company_id", "year"], how="left", suffixes=("", "_bs"))
    merged = merged.merge(cf_df, on=["company_id", "year"], how="left", suffixes=("", "_cf"))

    logger.info(f"Merged dataset: {len(merged)} company-year rows.")

    # Step 4: Edge case log and output structures
    opm_mismatches = []
    capital_allocation_rows = []
    sector_roce_notes = []

    # Step 5: Compute per-company-year ratios
    ratio_records = []

    for company_id, company_df in merged.groupby("company_id"):
        company_df = company_df.sort_values("year")
        is_financial = company_id in financials_companies

        # Build CAGR year maps (company-wide time series)
        sales_map = build_year_map(company_df["sales"], company_df["year"])
        pat_map = build_year_map(company_df["net_profit"], company_df["year"])
        eps_map = build_year_map(company_df["eps"], company_df["year"])

        for _, row in company_df.iterrows():
            year = int(row["year"])
            rec = {"company_id": company_id, "year": year}

            # --- P&L Fields ---
            sales = safe_float(row.get("sales"))
            operating_profit = safe_float(row.get("operating_profit"))
            opm_src = safe_float(row.get("opm_percentage"))
            other_income = safe_float(row.get("other_income"))
            interest = safe_float(row.get("interest"))
            depreciation = safe_float(row.get("depreciation"))
            net_profit = safe_float(row.get("net_profit"))
            eps = safe_float(row.get("eps"))
            dividend_payout = safe_float(row.get("dividend_payout"))

            # --- BS Fields ---
            equity_capital = safe_float(row.get("equity_capital"))
            reserves = safe_float(row.get("reserves"))
            borrowings = safe_float(row.get("borrowings"))
            total_assets = safe_float(row.get("total_assets"))
            investments = safe_float(row.get("investments"))

            # --- CF Fields ---
            cfo = safe_float(row.get("operating_activity"))
            cfi = safe_float(row.get("investing_activity"))
            cff = safe_float(row.get("financing_activity"))

            # === Profitability Ratios ===
            npm = calculate_net_profit_margin(net_profit, sales)
            opm, opm_mismatch = calculate_opm(operating_profit, sales, opm_src)
            roe = calculate_roe(net_profit, equity_capital, reserves)
            # EBIT = operating_profit + other_income (approximation from available data)
            ebit = (operating_profit or 0) + (other_income or 0)
            roce = calculate_roce(ebit, equity_capital, reserves, borrowings)
            roa = calculate_roa(net_profit, total_assets)

            rec["net_profit_margin_pct"] = npm
            rec["operating_profit_margin_pct"] = opm
            rec["return_on_equity_pct"] = roe
            rec["roce_pct"] = roce
            rec["return_on_assets_pct"] = roa

            # OPM cross-check logging
            if opm_mismatch:
                opm_mismatches.append({
                    "company_id": company_id,
                    "year": year,
                    "metric": "operating_profit_margin_pct",
                    "source_value": opm_mismatch["source_opm"],
                    "calculated_value": opm_mismatch["computed_opm"],
                    "difference": opm_mismatch["difference"],
                    "category": "data source issue",
                    "explanation": f"Computed OPM ({opm_mismatch['computed_opm']:.2f}%) differs from source opm_percentage ({opm_mismatch['source_opm']:.2f}%) by {opm_mismatch['difference']:.2f}%",
                })

            # === Leverage & Efficiency Ratios ===
            de_ratio, high_lev_flag = calculate_debt_to_equity(borrowings, equity_capital, reserves, is_financial)
            icr, icr_label, icr_warn = calculate_interest_coverage(operating_profit, other_income, interest)
            net_debt = calculate_net_debt(borrowings, investments)
            asset_turn = calculate_asset_turnover(sales, total_assets)

            rec["debt_to_equity"] = de_ratio
            rec["high_leverage_flag"] = int(high_lev_flag) if high_lev_flag is not None else 0
            rec["interest_coverage"] = icr
            rec["icr_label"] = icr_label
            rec["icr_warning_flag"] = int(icr_warn) if icr_warn is not None else 0
            rec["net_debt_cr"] = net_debt
            rec["asset_turnover"] = asset_turn

            # === Cash Flow KPIs ===
            fcf = calculate_free_cash_flow(cfo, cfi)
            capex_pct, capex_label = calculate_capex_intensity(cfi, sales)
            fcf_conv = calculate_fcf_conversion(fcf, operating_profit)

            # CFO Quality (5-year rolling)
            cfo_pat_ratios = compute_cfo_pat_ratios(
                company_df["operating_activity"],
                company_df["net_profit"],
                company_df["year"],
                year,
                window=5,
            )
            cfo_quality_score, cfo_quality_label = calculate_cfo_quality(cfo_pat_ratios)

            rec["free_cash_flow_cr"] = fcf
            rec["cfo_quality_score"] = cfo_quality_score
            rec["cfo_quality_label"] = cfo_quality_label
            rec["capex_cr"] = abs(cfi) if cfi is not None else None
            rec["capex_intensity_pct"] = capex_pct
            rec["capex_intensity_label"] = capex_label
            rec["fcf_conversion_pct"] = fcf_conv

            # Capital Allocation Pattern
            cfo_pat_current = cfo_pat_ratios[-1] if cfo_pat_ratios else None
            cfo_sign, cfi_sign, cff_sign, pattern_label = classify_capital_allocation(
                cfo, cfi, cff, cfo_pat_current
            )
            rec["capital_allocation_pattern"] = pattern_label
            capital_allocation_rows.append({
                "company_id": company_id,
                "year": year,
                "cfo_sign": cfo_sign,
                "cfi_sign": cfi_sign,
                "cff_sign": cff_sign,
                "pattern_label": pattern_label,
            })

            # === Supplementary KPI fields ===
            rec["earnings_per_share"] = eps
            rec["book_value_per_share"] = calculate_book_value_per_share(equity_capital, reserves, net_profit, eps)
            rec["dividend_payout_ratio_pct"] = dividend_payout
            rec["total_debt_cr"] = borrowings
            rec["cash_from_operations_cr"] = cfo

            # === CAGR: Revenue ===
            for n in [3, 5, 10]:
                val, flag = calculate_series_cagr(sales_map, year, n)
                rec[f"revenue_cagr_{n}yr"] = val
                if n == 5:
                    rec["revenue_cagr_5yr_flag"] = flag if flag != "NORMAL" else None

            # === CAGR: PAT ===
            for n in [3, 5, 10]:
                val, flag = calculate_series_cagr(pat_map, year, n)
                rec[f"pat_cagr_{n}yr"] = val
                if n == 5:
                    rec["pat_cagr_5yr_flag"] = flag if flag != "NORMAL" else None

            # === CAGR: EPS ===
            for n in [3, 5, 10]:
                val, flag = calculate_series_cagr(eps_map, year, n)
                rec[f"eps_cagr_{n}yr"] = val
                if n == 5:
                    rec["eps_cagr_5yr_flag"] = flag if flag != "NORMAL" else None

            # Placeholder for composite_quality_score (computed after all rows)
            rec["composite_quality_score"] = None

            ratio_records.append(rec)

    logger.info(f"Computed KPIs for {len(ratio_records)} company-year records.")

    # Step 6: Compute composite quality scores across all records
    records_df = pd.DataFrame(ratio_records)
    records_df = compute_percentile_scores(records_df)
    logger.info("Composite quality scores computed.")

    # Step 7: Insert all records into SQLite financial_ratios table
    cursor = conn.cursor()
    inserted = 0
    for rec in records_df.to_dict(orient="records"):
        cursor.execute("""
            INSERT OR REPLACE INTO financial_ratios (
                company_id, year,
                net_profit_margin_pct, operating_profit_margin_pct, return_on_equity_pct,
                roce_pct, return_on_assets_pct,
                debt_to_equity, high_leverage_flag,
                interest_coverage, icr_label, icr_warning_flag,
                net_debt_cr, asset_turnover,
                free_cash_flow_cr, cfo_quality_score, cfo_quality_label,
                capex_cr, capex_intensity_pct, capex_intensity_label,
                fcf_conversion_pct, capital_allocation_pattern,
                earnings_per_share, book_value_per_share, dividend_payout_ratio_pct,
                total_debt_cr, cash_from_operations_cr,
                revenue_cagr_3yr, revenue_cagr_5yr, revenue_cagr_10yr, revenue_cagr_5yr_flag,
                pat_cagr_3yr, pat_cagr_5yr, pat_cagr_10yr, pat_cagr_5yr_flag,
                eps_cagr_3yr, eps_cagr_5yr, eps_cagr_10yr, eps_cagr_5yr_flag,
                composite_quality_score
            ) VALUES (
                :company_id, :year,
                :net_profit_margin_pct, :operating_profit_margin_pct, :return_on_equity_pct,
                :roce_pct, :return_on_assets_pct,
                :debt_to_equity, :high_leverage_flag,
                :interest_coverage, :icr_label, :icr_warning_flag,
                :net_debt_cr, :asset_turnover,
                :free_cash_flow_cr, :cfo_quality_score, :cfo_quality_label,
                :capex_cr, :capex_intensity_pct, :capex_intensity_label,
                :fcf_conversion_pct, :capital_allocation_pattern,
                :earnings_per_share, :book_value_per_share, :dividend_payout_ratio_pct,
                :total_debt_cr, :cash_from_operations_cr,
                :revenue_cagr_3yr, :revenue_cagr_5yr, :revenue_cagr_10yr, :revenue_cagr_5yr_flag,
                :pat_cagr_3yr, :pat_cagr_5yr, :pat_cagr_10yr, :pat_cagr_5yr_flag,
                :eps_cagr_3yr, :eps_cagr_5yr, :eps_cagr_10yr, :eps_cagr_5yr_flag,
                :composite_quality_score
            )
        """, rec)
        inserted += 1

    conn.commit()
    logger.info(f"Inserted {inserted} rows into financial_ratios table.")

    # Step 8: Export capital_allocation.csv
    with open(CAPITAL_ALLOC_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"])
        writer.writeheader()
        writer.writerows(capital_allocation_rows)
    logger.info(f"Exported capital_allocation.csv with {len(capital_allocation_rows)} rows.")

    # Step 9: Log OPM edge cases
    if opm_mismatches:
        logger.info(f"OPM cross-check anomalies logged: {len(opm_mismatches)}")
        for m in opm_mismatches:
            logger.warning(
                f"OPM_MISMATCH | {m['company_id']} | Year:{m['year']} | "
                f"Source:{m['source_value']:.2f}% | Computed:{m['calculated_value']:.2f}% | "
                f"Diff:{m['difference']:.2f}% | {m['category']} | {m['explanation']}"
            )
    else:
        logger.info("No OPM cross-check anomalies detected.")

    # Step 10: Bank/NBFC ROCE Sector Benchmarking (Day 13)
    financials_df = records_df[records_df["company_id"].isin(financials_companies)].copy()
    if not financials_df.empty:
        for year, year_df in financials_df.groupby("year"):
            if year_df["roce_pct"].notnull().any():
                sector_median = year_df["roce_pct"].median()
                sector_p25 = year_df["roce_pct"].quantile(0.25)
                sector_p75 = year_df["roce_pct"].quantile(0.75)
                for _, row in year_df.iterrows():
                    if pd.notna(row["roce_pct"]):
                        sector_roce_notes.append({
                            "company_id": row["company_id"],
                            "year": year,
                            "computed_roce_pct": round(row["roce_pct"], 4),
                            "sector_median_roce": round(sector_median, 4),
                            "sector_p25_roce": round(sector_p25, 4),
                            "sector_p75_roce": round(sector_p75, 4),
                            "above_median": "Yes" if row["roce_pct"] >= sector_median else "No",
                            "note": "Financials sector-relative benchmark (D/E high-leverage flag suppressed)",
                        })

    with open(SECTOR_ROCE_NOTES_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["company_id", "year", "computed_roce_pct", "sector_median_roce",
                      "sector_p25_roce", "sector_p75_roce", "above_median", "note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sector_roce_notes)
    logger.info(f"Exported sector_roce_notes.csv with {len(sector_roce_notes)} rows.")

    # Step 11: Cross-check computed ROE vs companies.roe_percentage (Day 13)
    logger.info("Cross-checking computed ROE vs source roe_percentage from companies table...")
    for _, comp_row in companies_df.iterrows():
        cid = comp_row["company_id"]
        src_roe = safe_float(comp_row.get("roe_percentage"))
        if src_roe is None:
            continue
        # Get the latest year's computed ROE for this company
        comp_ratios = records_df[records_df["company_id"] == cid].sort_values("year", ascending=False)
        if comp_ratios.empty:
            continue
        latest_roe = safe_float(comp_ratios.iloc[0]["return_on_equity_pct"])
        if latest_roe is None:
            continue
        roe_diff = abs(latest_roe - src_roe)
        if roe_diff > 5.0:
            logger.warning(
                f"ROE_ANOMALY | {cid} | Source roe_percentage:{src_roe:.4f} | "
                f"Computed ROE (latest year):{latest_roe:.4f} | Diff:{roe_diff:.4f} | "
                f"category: version difference | explanation: Computed annual ROE ({latest_roe:.2f}%) differs from companies table static snapshot roe_percentage ({src_roe:.2f}%) by {roe_diff:.2f}% due to TTM vs annual fiscal year period."
            )

    # Step 12: Cross-check computed ROCE vs companies.roce_percentage (Day 13)
    logger.info("Cross-checking computed ROCE vs source roce_percentage from companies table...")
    for _, comp_row in companies_df.iterrows():
        cid = comp_row["company_id"]
        src_roce = safe_float(comp_row.get("roce_percentage"))
        if src_roce is None:
            continue
        comp_ratios = records_df[records_df["company_id"] == cid].sort_values("year", ascending=False)
        if comp_ratios.empty:
            continue
        latest_roce = safe_float(comp_ratios.iloc[0]["roce_pct"])
        if latest_roce is None:
            continue
        roce_diff = abs(latest_roce - src_roce)
        if roce_diff > 5.0:
            logger.warning(
                f"ROCE_ANOMALY | {cid} | Source roce_percentage:{src_roce:.4f} | "
                f"Computed ROCE (latest year):{latest_roce:.4f} | Diff:{roce_diff:.4f} | "
                f"category: version difference | explanation: Computed annual ROCE ({latest_roce:.2f}%) differs from companies table static snapshot roce_percentage ({src_roce:.2f}%) by {roce_diff:.2f}% due to TTM vs annual fiscal year period."
            )

    # Final verification
    count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    logger.info("=" * 60)
    logger.info(f"DONE — financial_ratios table row count: {count}")
    logger.info(f"Outputs written to: {OUTPUT_DIR}")
    logger.info("=" * 60)

    conn.close()


if __name__ == "__main__":
    run_ratio_engine()
