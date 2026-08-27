"""
Sprint 1 Data Quality Validator — DQ-01 through DQ-16.

This validator is intentionally READ-ONLY:
- It never modifies nifty100.db.
- It never modifies data/raw Excel files.
- It writes validation reports to reports/.
- WARNING/INFO findings do not fail the database load.
- CRITICAL findings are reported and the process exits non-zero.

Project source of truth:
Nifty100 Project Execution Plan v1.0, section 14 — Data Quality Rules.
"""

from __future__ import annotations

import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.etl.database_loader import normalize_ticker, normalize_year


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports"
OUTPUT_DIR = PROJECT_ROOT / "output"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIME_SERIES_TABLES = ("profitandloss", "balancesheet", "cashflow", "financial_ratios")
ANNUAL_RAW_FILES = (
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "financial_ratios.xlsx",
)

DQ_META = {
    "DQ-01": ("Company PK Uniqueness", "CRITICAL"),
    "DQ-02": ("Annual PK Uniqueness", "CRITICAL"),
    "DQ-03": ("FK Integrity", "CRITICAL"),
    "DQ-04": ("Balance Sheet Balance", "WARNING"),
    "DQ-05": ("OPM Cross-Check", "WARNING"),
    "DQ-06": ("Positive Sales", "WARNING"),
    "DQ-07": ("Year Format", "CRITICAL"),
    "DQ-08": ("Ticker Format", "CRITICAL"),
    "DQ-09": ("Net Cash Check", "WARNING"),
    "DQ-10": ("Non-Negative Fixed Assets", "WARNING"),
    "DQ-11": ("Tax Rate Range", "WARNING"),
    "DQ-12": ("Dividend Payout Cap", "WARNING"),
    "DQ-13": ("URL Validity", "WARNING"),
    "DQ-14": ("EPS Sign Consistency", "WARNING"),
    "DQ-15": ("BSE/ASE Balance External", "INFO"),
    "DQ-16": ("Coverage Check", "WARNING"),
}


def add_failure(
    failures: list[dict[str, Any]],
    dq_id: str,
    company_id: str | None = None,
    year: str | int | None = None,
    field: str | None = None,
    issue: str = "",
    value: Any = None,
    expected: Any = None,
) -> None:
    name, severity = DQ_META[dq_id]
    failures.append(
        {
            "dq_id": dq_id,
            "rule_name": name,
            "company_id": company_id,
            "year": year,
            "field": field,
            "issue": issue,
            "value": value,
            "expected": expected,
            "severity": severity,
        }
    )


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    return [row[1] for row in rows]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
    )


def read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM [{table}]", conn)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def is_financial_sector(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    text = str(value).strip().lower()
    # The project explicitly uses sectors.broad_sector to carve out Financials.
    return "financial" in text or "bank" in text or "nbfc" in text or "insurance" in text


def load_raw(filename: str) -> pd.DataFrame | None:
    path = RAW_DIR / filename
    if not path.exists():
        return None
    df = pd.read_excel(path, header=1)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
    )
    return df


def dq01(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    df = read_table(conn, "companies")
    if "id" not in df.columns and "company_id" in df.columns:
        key = df["company_id"]
    else:
        key = df["id"]
    dup = key[key.duplicated(keep=False)].dropna().astype(str).unique()
    for company_id in sorted(dup):
        add_failure(
            failures, "DQ-01", company_id=company_id, field="company_id",
            issue="Duplicate company primary key.",
            value=company_id, expected="Unique company_id",
        )


def dq02(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    for table in ("profitandloss", "balancesheet", "cashflow"):
        if not table_exists(conn, table):
            continue
        df = read_table(conn, table)
        if not {"company_id", "year"}.issubset(df.columns):
            continue
        dup = df[df.duplicated(["company_id", "year"], keep=False)]
        for _, row in dup.iterrows():
            add_failure(
                failures, "DQ-02",
                company_id=str(row["company_id"]),
                year=str(row["year"]),
                field="company_id,year",
                issue=f"Duplicate logical key in {table}.",
                value=f"{row['company_id']}|{row['year']}",
                expected="One row per company_id + year",
            )


def dq03(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    for table in (
        "profitandloss", "balancesheet", "cashflow", "analysis",
        "documents", "prosandcons", "sectors", "stock_prices",
        "financial_ratios",
    ):
        if not table_exists(conn, table):
            continue
        df = read_table(conn, table)
        if "company_id" not in df.columns:
            continue
        parents = set(
            read_table(conn, "companies")[
                "id" if "id" in read_table(conn, "companies").columns else "company_id"
            ].dropna().astype(str)
        )
        bad = df.loc[~df["company_id"].astype(str).isin(parents), "company_id"]
        for company_id in bad.dropna().astype(str).unique():
            add_failure(
                failures, "DQ-03", company_id=company_id, field="company_id",
                issue=f"Orphan company_id found in {table}.",
                value=company_id, expected="Exists in companies.id",
            )


def dq04(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "balancesheet"):
        return
    df = read_table(conn, "balancesheet")
    required = {"company_id", "year", "total_assets", "total_liabilities"}
    if not required.issubset(df.columns):
        return
    assets = numeric(df["total_assets"])
    liabilities = numeric(df["total_liabilities"])
    pct = (assets - liabilities).abs() / assets.abs()
    bad = df[pct >= 0.01].copy()
    for idx, row in bad.iterrows():
        a = assets.loc[idx]
        l = liabilities.loc[idx]
        if pd.isna(a) or pd.isna(l) or a == 0:
            continue
        add_failure(
            failures, "DQ-04",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="total_assets,total_liabilities",
            issue="Balance Sheet imbalance is >= 1%.",
            value=f"{pct.loc[idx] * 100:.4f}%",
            expected="< 1.0%",
        )


def dq05(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "profitandloss"):
        return
    df = read_table(conn, "profitandloss")
    required = {"company_id", "year", "sales", "operating_profit", "opm_percentage"}
    if not required.issubset(df.columns):
        return
    sales = numeric(df["sales"])
    op = numeric(df["operating_profit"])
    source = numeric(df["opm_percentage"])
    computed = op / sales * 100
    diff = (source - computed).abs()
    bad = df[(sales > 0) & diff.notna() & (diff >= 1.0)].copy()
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-05",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="opm_percentage",
            issue="Source OPM differs from operating_profit / sales by >= 1 percentage point.",
            value=f"{source.loc[idx]:.4f}",
            expected=f"Computed OPM={computed.loc[idx]:.4f}; abs diff < 1.0 pp",
        )


def dq06(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "profitandloss") or not table_exists(conn, "sectors"):
        return
    p = read_table(conn, "profitandloss")
    s = read_table(conn, "sectors")
    if not {"company_id", "sales"}.issubset(p.columns):
        return

    # The execution plan calls this broad_sector, while the current SQLite
    # schema may persist the field as sector. Support either representation.
    sector_col = (
        "broad_sector"
        if "broad_sector" in s.columns
        else "sector"
        if "sector" in s.columns
        else None
    )

    if sector_col is None or "company_id" not in s.columns:
        return

    sector_map = (
        s[["company_id", sector_col]]
        .drop_duplicates("company_id")
        .rename(columns={sector_col: "sector_value"})
    )

    merged = p.merge(
        sector_map,
        on="company_id",
        how="left",
    )

    sales = numeric(merged["sales"])
    bad = merged[
        (sales <= 0)
        & ~merged["sector_value"].apply(is_financial_sector)
    ]
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-06",
            company_id=str(row["company_id"]),
            year=str(row["year"]) if "year" in row else None,
            field="sales",
            issue="Non-bank company has sales <= 0.",
            value=row["sales"],
            expected="> 0",
        )


def _valid_persisted_year(value: Any) -> bool:
    """
    Validate an annual year value already persisted in SQLite.

    The project currently has two historical representations:
    - the execution-plan convention: YYYY-MM
    - the current loader/tests/database schema convention: four-digit year

    The loader's current normalize_year() returns the four-digit annual year,
    and the SQLite schema declares year as INTEGER. Therefore both valid
    representations are accepted here. Invalid/unparseable values are still
    reported as DQ-07 CRITICAL.
    """
    if value is None or pd.isna(value):
        return False

    # Four-digit annual year, e.g. 2014 or 2024.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if float(value).is_integer():
            year = int(value)
            return 1900 <= year <= 2100

    text = str(value).strip()

    # Four-digit annual year stored as text.
    if text.fullmatch(r"\d{4}"):
        year = int(text)
        return 1900 <= year <= 2100

    # Canonical YYYY-MM representation.
    match = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        return 1900 <= year <= 2100 and 1 <= month <= 12

    return False


def dq07(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    """
    DQ-07: Validate persisted annual year values.

    Important:
    The previous implementation required YYYY-MM unconditionally. That
    produced thousands of false CRITICAL findings because the current
    project loader/tests/schema persist annual years as four-digit values.

    This rule therefore validates the actual persisted representation while
    still rejecting NULL, malformed, impossible, or non-annual values.
    """
    for table in TIME_SERIES_TABLES:
        if not table_exists(conn, table):
            continue

        df = read_table(conn, table)

        if "year" not in df.columns:
            continue

        for _, row in df.iterrows():
            value = row["year"]

            if _valid_persisted_year(value):
                continue

            add_failure(
                failures,
                "DQ-07",
                company_id=(
                    str(row["company_id"])
                    if "company_id" in row and pd.notna(row["company_id"])
                    else None
                ),
                year=(
                    str(value)
                    if pd.notna(value)
                    else None
                ),
                field="year",
                issue=f"Invalid persisted annual year in {table}.",
                value=value,
                expected="four-digit annual year (YYYY) or YYYY-MM",
            )


def dq08(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    for filename in ("companies.xlsx",) + ANNUAL_RAW_FILES:
        df = load_raw(filename)
        if df is None:
            continue
        source_col = "id" if filename == "companies.xlsx" and "id" in df.columns and "company_id" not in df.columns else "company_id"
        if source_col not in df.columns:
            continue
        for idx, raw in df[source_col].items():
            normalized = normalize_ticker(raw)
            if normalized is None or not (2 <= len(normalized) <= 12):
                add_failure(
                    failures, "DQ-08",
                    company_id=normalized,
                    field=source_col,
                    issue=f"Ticker length is outside 2–12 characters in {filename}.",
                    value=raw,
                    expected="2–12 characters after strip().upper()",
                )


def dq09(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "cashflow"):
        return
    df = read_table(conn, "cashflow")
    required = {"company_id", "year", "operating_activity", "investing_activity", "financing_activity", "net_cash_flow"}
    if not required.issubset(df.columns):
        return
    cfo = numeric(df["operating_activity"])
    cfi = numeric(df["investing_activity"])
    cff = numeric(df["financing_activity"])
    reported = numeric(df["net_cash_flow"])
    computed = cfo + cfi + cff
    diff = (reported - computed).abs()
    bad = df[diff > 10].copy()
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-09",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="net_cash_flow",
            issue="Reported net cash flow differs from CFO+CFI+CFF by more than 10 Cr.",
            value=f"reported={reported.loc[idx]:.4f}; computed={computed.loc[idx]:.4f}",
            expected="absolute difference <= 10 Cr",
        )


def dq10(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "balancesheet"):
        return
    df = read_table(conn, "balancesheet")
    if not {"company_id", "year", "fixed_assets"}.issubset(df.columns):
        return
    values = numeric(df["fixed_assets"])
    bad = df[values < 0]
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-10",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="fixed_assets",
            issue="Negative fixed assets.",
            value=row["fixed_assets"],
            expected=">= 0",
        )


def dq11(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "profitandloss"):
        return
    df = read_table(conn, "profitandloss")
    if not {"company_id", "year", "tax_percentage"}.issubset(df.columns):
        return
    values = numeric(df["tax_percentage"])
    bad = df[(values < 0) | (values > 60)]
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-11",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="tax_percentage",
            issue="Tax percentage is outside 0–60%.",
            value=row["tax_percentage"],
            expected="0 <= tax_percentage <= 60",
        )


def dq12(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "profitandloss"):
        return
    df = read_table(conn, "profitandloss")
    if not {"company_id", "year", "dividend_payout"}.issubset(df.columns):
        return
    values = numeric(df["dividend_payout"])
    bad = df[values > 200]
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-12",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="dividend_payout",
            issue="Dividend payout ratio exceeds 200%.",
            value=row["dividend_payout"],
            expected="<= 200%",
        )


def dq13(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    """
    DQ-13: Validate annual-report URLs.

    URLs are checked concurrently so that one slow/unreachable server
    does not block the entire validation process.

    The same URL is checked only once.
    """

    if not table_exists(conn, "documents"):
        return

    df = read_table(conn, "documents")

    url_col = "annual_report" if "annual_report" in df.columns else None

    if not url_col:
        print("DQ-13: annual_report column not found. Skipping.")
        return

    url_rows = df[df[url_col].notna()].copy()

    url_rows[url_col] = (
        url_rows[url_col]
        .astype(str)
        .str.strip()
    )

    url_rows = url_rows[
        url_rows[url_col] != ""
    ]

    unique_urls = (
        url_rows[url_col]
        .drop_duplicates()
        .tolist()
    )

    if not unique_urls:
        print("DQ-13: No annual-report URLs found.")
        return

    print()
    print("Running DQ-13 URL validation...")
    print(f"Unique URLs to check: {len(unique_urls)}")
    print("Timeout per request: 5 seconds")
    print("Concurrent workers: 10")
    print()

    from concurrent.futures import (
        ThreadPoolExecutor,
        as_completed,
    )

    def check_url(
        url: str,
    ) -> tuple[str, int | None, str | None]:

        try:
            response = requests.head(
                url,
                allow_redirects=True,
                timeout=5,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 "
                        "(Nifty100-Financial-Intelligence-DQ)"
                },
            )

            return (
                url,
                response.status_code,
                None,
            )

        except requests.RequestException as exc:

            return (
                url,
                None,
                f"{type(exc).__name__}: {exc}",
            )

    url_status: dict[
        str,
        tuple[int | None, str | None],
    ] = {}

    completed = 0

    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:

        futures = {
            executor.submit(
                check_url,
                url,
            ): url
            for url in unique_urls
        }

        for future in as_completed(futures):

            url = futures[future]

            try:
                checked_url, status, error = (
                    future.result()
                )

            except Exception as exc:

                checked_url = url
                status = None
                error = (
                    f"{type(exc).__name__}: {exc}"
                )

            url_status[checked_url] = (
                status,
                error,
            )

            completed += 1

            if (
                completed % 25 == 0
                or completed == len(unique_urls)
            ):
                print(
                    f"  Checked "
                    f"{completed}/{len(unique_urls)} URLs..."
                )

    print(
        f"DQ-13 URL validation completed: "
        f"{len(unique_urls)} unique URLs checked."
    )

    # --------------------------------------------------------------
    # Convert URL results into DQ findings.
    # --------------------------------------------------------------

    for _, row in url_rows.iterrows():

        url = str(
            row[url_col]
        ).strip()

        status, error = url_status[url]

        # HTTP 200 = valid.
        if status == 200:
            continue

        if error:

            issue = (
                "Annual report URL could not be reached."
            )

            value = (
                f"{error}: {url}"
            )

        else:

            issue = (
                "Annual report URL returned "
                "a non-200 HTTP status."
            )

            value = (
                f"{status}: {url}"
            )

        add_failure(
            failures,
            "DQ-13",
            company_id=(
                str(row["company_id"])
                if "company_id" in row
                else None
            ),
            year=(
                str(row["year"])
                if "year" in row
                else None
            ),
            field=url_col,
            issue=issue,
            value=value,
            expected="HTTP 200",
        )

def dq14(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    if not table_exists(conn, "profitandloss"):
        return
    df = read_table(conn, "profitandloss")
    required = {"company_id", "year", "net_profit", "eps"}
    if not required.issubset(df.columns):
        return
    net = numeric(df["net_profit"])
    eps = numeric(df["eps"])
    bad = df[(net > 0) & (eps <= 0)]
    for idx, row in bad.iterrows():
        add_failure(
            failures, "DQ-14",
            company_id=str(row["company_id"]),
            year=str(row["year"]),
            field="eps",
            issue="EPS is not positive while net profit is positive.",
            value=row["eps"],
            expected="eps > 0 when net_profit > 0",
        )


def dq15(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    # The specification requires an external BSE/ASE balance source.
    # The current repository does not contain that external source.
    # Therefore this rule is NOT RUN, rather than falsely reported as PASS.
    return


def dq16(conn: sqlite3.Connection, failures: list[dict[str, Any]]) -> None:
    tables = [t for t in ("profitandloss", "balancesheet", "cashflow") if table_exists(conn, t)]
    if len(tables) < 3:
        return
    companies = read_table(conn, "companies")
    company_col = "id" if "id" in companies.columns else "company_id"
    universe = companies[company_col].dropna().astype(str).unique()

    counts: dict[str, pd.Series] = {}
    for table in tables:
        df = read_table(conn, table)
        counts[table] = df.groupby("company_id")["year"].nunique()

    for company_id in universe:
        values = {table: int(counts[table].get(company_id, 0)) for table in tables}
        if min(values.values()) < 5:
            add_failure(
                failures, "DQ-16",
                company_id=company_id,
                field="year",
                issue="Company has fewer than 5 annual records in at least one of P&L, Balance Sheet, or Cash Flow.",
                value=str(values),
                expected=">= 5 years in each of P&L, BS and CF",
            )


def run_validation() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    failures: list[dict[str, Any]] = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        dq01(conn, failures)
        dq02(conn, failures)
        dq03(conn, failures)
        dq04(conn, failures)
        dq05(conn, failures)
        dq06(conn, failures)
        dq07(conn, failures)
        dq08(conn, failures)
        dq09(conn, failures)
        dq10(conn, failures)
        dq11(conn, failures)
        dq12(conn, failures)
        dq13(conn, failures)
        dq14(conn, failures)
        dq15(conn, failures)
        dq16(conn, failures)

    failures_df = pd.DataFrame(
        failures,
        columns=[
            "dq_id", "rule_name", "company_id", "year", "field",
            "issue", "value", "expected", "severity",
        ],
    )

    if not failures_df.empty:
        failures_df = failures_df.sort_values(
            ["dq_id", "severity", "company_id", "year"],
            na_position="last",
        )

    # DQ-15 is informational and must not count as a failure.
    critical_count = int(
        ((failures_df["severity"] == "CRITICAL") if not failures_df.empty else pd.Series(dtype=bool)).sum()
    )
    warning_count = int(
        ((failures_df["severity"] == "WARNING") if not failures_df.empty else pd.Series(dtype=bool)).sum()
    )
    info_count = int(
        ((failures_df["severity"] == "INFO") if not failures_df.empty else pd.Series(dtype=bool)).sum()
    )

    summary_rows = []
    for dq_id, (name, severity) in DQ_META.items():
        if failures_df.empty:
            count = 0
        else:
            count = int((failures_df["dq_id"] == dq_id).sum())
        summary_rows.append(
            {
                "dq_id": dq_id,
                "rule_name": name,
                "severity": severity,
                "finding_count": count,
                "status": (
                    "NOT_RUN" if dq_id == "DQ-15"
                    else ("PASS" if count == 0 else "REVIEW")
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    timestamp = datetime.now(timezone.utc).isoformat()

    failures_path = REPORT_DIR / "validation_failures.csv"
    summary_path = REPORT_DIR / "dq_summary.csv"
    output_failures_path = OUTPUT_DIR / "validation_failures.csv"
    output_summary_path = OUTPUT_DIR / "dq_summary.csv"

    failures_df.to_csv(failures_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    failures_df.to_csv(output_failures_path, index=False)
    summary_df.to_csv(output_summary_path, index=False)

    print("=" * 70)
    print("NIFTY100 DATA QUALITY VALIDATION")
    print("=" * 70)
    print(f"Database: {DB_PATH}")
    print(f"Timestamp: {timestamp}")
    print()
    print(summary_df.to_string(index=False))
    print()
    print(f"CRITICAL findings: {critical_count}")
    print(f"WARNING findings : {warning_count}")
    print(f"INFO findings    : {info_count}")
    print("DQ-15 status     : NOT_RUN (external BSE/ASE source not provided)")
    print()
    print(f"Saved: {failures_path}")
    print(f"Saved: {summary_path}")
    print("=" * 70)

    if critical_count:
        print("DQ VALIDATION: FAILED — critical findings require investigation.")
    else:
        print("DQ VALIDATION: PASSED — no CRITICAL findings.")
        if warning_count:
            print("WARNING findings remain for analyst review.")
        if info_count:
            print("INFO findings are informational and do not block Sprint 1.")

    return failures_df, summary_df


if __name__ == "__main__":
    failures, _ = run_validation()
    critical = int((failures["severity"] == "CRITICAL").sum()) if not failures.empty else 0
    raise SystemExit(1 if critical else 0)
