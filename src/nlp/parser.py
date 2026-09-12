r"""
Analysis Text Parser & NLP Metric Extractor (Sprint 5 — Day 29).

Parses semi-structured text fields from analysis.xlsx:
- compounded_sales_growth
- compounded_profit_growth
- stock_price_cagr
- roe

Uses regex: r"(\d+)\s*Years?:?\s*([\d.]+)%" to extract:
- period_years (e.g. 10)
- value_pct (e.g. 21.0)

Generates:
- output/analysis_parsed.csv (columns: company_id, metric_type, period_years, value_pct)
- output/parse_failures.csv (columns: company_id, metric_type, raw_text, reason)
- Cross-validates parsed CAGR values against computed CAGR from financial_ratios table.
"""

import re
import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
RAW_ANALYSIS_PATH = PROJECT_ROOT / "data" / "raw" / "analysis.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Canonical Regex Pattern specified in Sprint 5 Day 29
CAGR_PATTERN = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%", re.IGNORECASE)

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]


def parse_text_cagr(text: Any) -> List[Tuple[int, float]]:
    """
    Parse text containing one or more 'X Years: Y%' statements.
    Returns list of (period_years, value_pct) tuples.
    """
    if pd.isna(text) or text is None:
        return []
    
    text_str = str(text).strip()
    if not text_str:
        return []

    matches = CAGR_PATTERN.findall(text_str)
    results = []
    for m in matches:
        try:
            period = int(m[0])
            val = float(m[1])
            results.append((period, val))
        except (ValueError, TypeError):
            continue
    return results


def load_raw_analysis() -> pd.DataFrame:
    """
    Load analysis data from raw excel or database.
    """
    # Priority: Database table first if populated with company_id tickers
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        df_db = pd.read_sql_query("SELECT * FROM analysis", conn)
        conn.close()
        if not df_db.empty and "company_id" in df_db.columns:
            return df_db

    if RAW_ANALYSIS_PATH.exists():
        try:
            raw = pd.read_excel(RAW_ANALYSIS_PATH)
            # If first row contains column headers
            if "company_id" not in [str(c).lower() for c in raw.columns]:
                raw = pd.read_excel(RAW_ANALYSIS_PATH, skiprows=1)
            raw.columns = [str(c).strip().lower().replace(" ", "_") for c in raw.columns]
            return raw
        except Exception:
            pass

    return pd.DataFrame()


def parse_analysis_file() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parse analysis records and return (parsed_df, failures_df).
    Saves outputs to output/analysis_parsed.csv and output/parse_failures.csv.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_raw_analysis()

    parsed_records: List[Dict[str, Any]] = []
    failure_records: List[Dict[str, Any]] = []

    if df.empty:
        parsed_df = pd.DataFrame(columns=["company_id", "metric_type", "period_years", "value_pct"])
        failures_df = pd.DataFrame(columns=["company_id", "metric_type", "raw_text", "reason"])
        parsed_df.to_csv(OUTPUT_DIR / "analysis_parsed.csv", index=False)
        failures_df.to_csv(OUTPUT_DIR / "parse_failures.csv", index=False)
        return parsed_df, failures_df

    # Ensure company_id column exists
    comp_col = next((c for c in df.columns if "company" in c or "ticker" in c or c == "id"), None)
    if not comp_col:
        comp_col = df.columns[0]

    for _, row in df.iterrows():
        cid = str(row[comp_col]).strip()
        for field in TARGET_FIELDS:
            # Find matching column
            col = next((c for c in df.columns if field in c or c.replace("_", "") == field.replace("_", "")), None)
            if not col or pd.isna(row[col]):
                continue

            raw_val = str(row[col]).strip()
            parsed = parse_text_cagr(raw_val)

            if parsed:
                for period, val in parsed:
                    parsed_records.append({
                        "company_id": cid,
                        "metric_type": field,
                        "period_years": period,
                        "value_pct": val
                    })
            else:
                failure_records.append({
                    "company_id": cid,
                    "metric_type": field,
                    "raw_text": raw_val,
                    "reason": "Pattern mismatch or empty value"
                })

    parsed_df = pd.DataFrame(parsed_records)
    if parsed_df.empty:
        parsed_df = pd.DataFrame(columns=["company_id", "metric_type", "period_years", "value_pct"])

    failures_df = pd.DataFrame(failure_records)
    if failures_df.empty:
        failures_df = pd.DataFrame(columns=["company_id", "metric_type", "raw_text", "reason"])

    parsed_df.to_csv(OUTPUT_DIR / "analysis_parsed.csv", index=False)
    failures_df.to_csv(OUTPUT_DIR / "parse_failures.csv", index=False)

    return parsed_df, failures_df


def cross_validate_cagr(parsed_df: pd.DataFrame, threshold_pct: float = 5.0) -> pd.DataFrame:
    """
    Cross-validate parsed CAGR values against computed CAGR metrics from financial_ratios table.
    Flags divergence > threshold_pct (default 5.0%).
    """
    if parsed_df.empty or not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(str(DB_PATH))
    # Fetch latest financial ratios
    ratios_df = pd.read_sql_query("""
        SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr, return_on_equity_pct
        FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    conn.close()

    divergences = []
    for _, row in parsed_df.iterrows():
        cid = row["company_id"]
        mtype = row["metric_type"]
        period = row["period_years"]
        parsed_val = row["value_pct"]

        # Only cross-validate 5-year periods or ROE
        comp_rows = ratios_df[ratios_df["company_id"] == cid]
        if comp_rows.empty:
            continue

        comp_val = None
        if mtype == "compounded_sales_growth" and period == 5:
            comp_val = comp_rows["revenue_cagr_5yr"].values[0]
        elif mtype == "compounded_profit_growth" and period == 5:
            comp_val = comp_rows["pat_cagr_5yr"].values[0]
        elif mtype == "roe":
            comp_val = comp_rows["return_on_equity_pct"].values[0]

        if comp_val is not None and pd.notna(comp_val):
            diff = abs(parsed_val - comp_val)
            divergences.append({
                "company_id": cid,
                "metric_type": mtype,
                "period_years": period,
                "parsed_value": parsed_val,
                "computed_value": round(float(comp_val), 2),
                "divergence_pct": round(diff, 2),
                "flag_manual_review": diff > threshold_pct
            })

    div_df = pd.DataFrame(divergences)
    if not div_df.empty:
        div_df.to_csv(OUTPUT_DIR / "cagr_divergences.csv", index=False)
    return div_df


if __name__ == "__main__":
    p_df, f_df = parse_analysis_file()
    print(f"Parsed records: {len(p_df)}")
    print(f"Parse failures: {len(f_df)}")
    div = cross_validate_cagr(p_df)
    print(f"Cross-validation comparisons: {len(div)}")
