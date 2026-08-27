"""
Database loader for Nifty 100 Financial Intelligence.

Loads normalized Excel source data into the SQLite database.

ETL flow:
    1. Read Excel source using the correct header row per file.
    2. Normalize column names.
    3. Normalize company IDs.
    4. Normalize annual year values.
    5. Normalize stock-price dates.
    6. Rename source columns to database columns.
    7. Filter companies outside the master company universe.
    8. Remove duplicate logical keys.
    9. Align source columns with the database schema.
    10. Validate required fields.
    11. Insert into SQLite.
    12. Run final integrity checks.
    13. Commit only when the complete load succeeds.

The raw Excel files are never modified.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
SUPPORTING_DIR = PROJECT_ROOT / "data" / "supporting"

DATABASE_PATH = PROJECT_ROOT / "nifty100.db"


# ============================================================================
# SOURCE FILE MAPPING
# ============================================================================

SOURCE_TO_TABLE = {
    "companies.xlsx": "companies",
    "profitandloss.xlsx": "profitandloss",
    "balancesheet.xlsx": "balancesheet",
    "cashflow.xlsx": "cashflow",
    "analysis.xlsx": "analysis",
    "documents.xlsx": "documents",
    "prosandcons.xlsx": "prosandcons",
    "sectors.xlsx": "sectors",
    "stock_prices.xlsx": "stock_prices",
    "financial_ratios.xlsx": "financial_ratios",
}


ORDERED_SOURCES = [
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
    "sectors.xlsx",
    "stock_prices.xlsx",
    "financial_ratios.xlsx",
]


# ============================================================================
# HEADER CONFIGURATION
# ============================================================================
#
# IMPORTANT:
#
# Most Bluestock source files contain one metadata row above the real header,
# so they require header=1.
#
# However, these three files are clean tabular exports where the first row
# is already the real header:
#
#   sectors.xlsx
#   stock_prices.xlsx
#   financial_ratios.xlsx
#
# Using header=1 for those files causes the first data row to become the
# column names and is therefore incorrect.
# ============================================================================

HEADER_ROW = {
    "companies.xlsx": 1,
    "profitandloss.xlsx": 1,
    "balancesheet.xlsx": 1,
    "cashflow.xlsx": 1,
    "analysis.xlsx": 1,
    "documents.xlsx": 1,
    "prosandcons.xlsx": 1,
    "sectors.xlsx": 0,
    "stock_prices.xlsx": 0,
    "financial_ratios.xlsx": 0,
}


# ============================================================================
# TABLE CATEGORIES
# ============================================================================

TIME_SERIES_TABLES = {
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
}


COMPANY_SNAPSHOT_TABLES = {
    "analysis",
    "sectors",
    "prosandcons",
}


# ============================================================================
# SOURCE -> DATABASE COLUMN MAPPINGS
# ============================================================================

# Documents:
#
# Excel:
#   id
#
# Database:
#   document_id
#
# Sectors:
#
# Excel                         Database
# broad_sector           ->     sector
# sub_sector             ->     industry
# index_weight_pct       ->     weight
#
# Stock prices:
#
# Excel:
#   date
#
# Database:
#   price_date
# ============================================================================

SOURCE_COLUMN_RENAMES = {
    "documents": {
        "id": "document_id",
    },
    "sectors": {
        "broad_sector": "sector",
        "sub_sector": "industry",
        "index_weight_pct": "weight",
    },
    "stock_prices": {
        "date": "price_date",
    },
}


# ============================================================================
# FINANCIAL RATIO MAPPING
# ============================================================================
#
# The source contains descriptive ratio names while the database schema
# intentionally uses generic ratio_1 ... ratio_13 columns.
# ============================================================================

FINANCIAL_RATIO_RENAMES = {
    "net_profit_margin_pct": "ratio_1",
    "operating_profit_margin_pct": "ratio_2",
    "return_on_equity_pct": "ratio_3",
    "debt_to_equity": "ratio_4",
    "interest_coverage": "ratio_5",
    "asset_turnover": "ratio_6",
    "free_cash_flow_cr": "ratio_7",
    "capex_cr": "ratio_8",
    "earnings_per_share": "ratio_9",
    "book_value_per_share": "ratio_10",
    "dividend_payout_ratio_pct": "ratio_11",
    "total_debt_cr": "ratio_12",
    "cash_from_operations_cr": "ratio_13",
}


# ============================================================================
# GENERAL HELPERS
# ============================================================================


def load_source_file(filename: str) -> pd.DataFrame:
    """
    Load one source Excel file using its configured header row.
    """

    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Source file not found: {path}"
        )

    header_row = HEADER_ROW[filename]

    print(
        f"  Reading {filename} from raw/ "
        f"(header={header_row})..."
    )

    return pd.read_excel(
        path,
        header=header_row,
    )


def normalize_column_names(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize DataFrame column names to lowercase snake_case.
    """

    result = df.copy()

    result.columns = (
        result.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    return result


def normalize_ticker(
    value: object,
) -> str | None:
    """
    Normalize company ticker.

    Examples:
        RELIANCE       -> RELIANCE
        reliance       -> RELIANCE
        ' TCS '        -> TCS
        None           -> None
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip().upper()

    if not text:
        return None

    return text


def normalize_year(
    value: object,
) -> int | None:
    """
    Normalize a financial year to a four-digit integer year.

    Examples:
        2023                 -> 2023
        2023.0               -> 2023
        "2023"               -> 2023
        "FY2023"             -> 2023
        "FY 2023"            -> 2023
        "FY2023-24"          -> 2023
        "Financial Year 2023"-> 2023
        "Dec 2023"           -> 2023
        "Mar-13"             -> 2013
        "TTM"                -> None

    The database schema defines year as INTEGER, therefore this function
    deliberately returns only the annual year.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if not text:
        return None

    upper_text = text.upper()

    # ------------------------------------------------------------------
    # Explicitly reject non-annual TTM values.
    # ------------------------------------------------------------------

    if upper_text in {
        "TTM",
        "TRAILING TWELVE MONTHS",
        "TRAILING 12 MONTHS",
    }:
        return None

    # ------------------------------------------------------------------
    # Numeric year.
    # ------------------------------------------------------------------

    numeric_year_match = re.fullmatch(
        r"(20\d{2})(?:\.0+)?",
        text,
    )

    if numeric_year_match:
        return int(
            numeric_year_match.group(1)
        )

    # ------------------------------------------------------------------
    # FY2023
    # FY 2023
    # FY2023-24
    # Financial Year 2023
    # ------------------------------------------------------------------

    fiscal_year_match = re.search(
        r"(?:FINANCIAL\s+YEAR|FY)"
        r"\s*[-/]?\s*"
        r"(20\d{2})",
        text,
        flags=re.IGNORECASE,
    )

    if fiscal_year_match:
        return int(
            fiscal_year_match.group(1)
        )

    # ------------------------------------------------------------------
    # Any explicit four-digit year in a textual label.
    #
    # Examples:
    #   Dec 2023
    #   Mar 2023 15
    #   Financial Year 2024
    # ------------------------------------------------------------------

    four_digit_year_match = re.search(
        r"\b(20\d{2})\b",
        text,
    )

    if four_digit_year_match:
        return int(
            four_digit_year_match.group(1)
        )

    # ------------------------------------------------------------------
    # Month + two-digit year.
    #
    # Examples:
    #   Mar-13
    #   Mar 13
    #   Dec-12
    # ------------------------------------------------------------------

    month_names = (
        "JAN|JANUARY|"
        "FEB|FEBRUARY|"
        "MAR|MARCH|"
        "APR|APRIL|"
        "MAY|"
        "JUN|JUNE|"
        "JUL|JULY|"
        "AUG|AUGUST|"
        "SEP|SEPT|SEPTEMBER|"
        "OCT|OCTOBER|"
        "NOV|NOVEMBER|"
        "DEC|DECEMBER"
    )

    month_two_digit_match = re.search(
        rf"\b(?:{month_names})"
        r"[\s\-/]*(\d{2})\b",
        text,
        flags=re.IGNORECASE,
    )

    if month_two_digit_match:
        two_digit_year = int(
            month_two_digit_match.group(1)
        )

        if two_digit_year <= 49:
            return 2000 + two_digit_year

        return 1900 + two_digit_year

    # ------------------------------------------------------------------
    # FY23
    # ------------------------------------------------------------------

    short_fy_match = re.fullmatch(
        r"FY\s*(\d{2})",
        text,
        flags=re.IGNORECASE,
    )

    if short_fy_match:
        two_digit_year = int(
            short_fy_match.group(1)
        )

        if two_digit_year <= 49:
            return 2000 + two_digit_year

        return 1900 + two_digit_year

    return None


def normalize_price_date(
    value: object,
) -> str | None:
    """
    Normalize stock-price date to YYYY-MM-DD.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.strftime("%Y-%m-%d")


# ============================================================================
# DATAFRAME PREPARATION
# ============================================================================


def prepare_dataframe(
    df: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """
    Normalize one source DataFrame.

    This function handles source-specific differences between Excel files
    and the normalized SQLite schema.
    """

    result = df.copy()

    # Remove completely empty rows.
    result = result.dropna(
        axis=0,
        how="all",
    )

    # Remove completely empty columns.
    result = result.dropna(
        axis=1,
        how="all",
    )

    # Normalize column names.
    result = normalize_column_names(
        result
    )

    # ------------------------------------------------------------------
    # Companies:
    #
    # Excel uses "id".
    # Database uses "company_id".
    # ------------------------------------------------------------------

    if table_name == "companies":

        if (
            "id" in result.columns
            and "company_id" not in result.columns
        ):
            result = result.rename(
                columns={
                    "id": "company_id"
                }
            )

    # ------------------------------------------------------------------
    # Normalize company IDs.
    # ------------------------------------------------------------------

    if "company_id" in result.columns:
        result["company_id"] = result[
            "company_id"
        ].apply(
            normalize_ticker
        )

    # ------------------------------------------------------------------
    # Normalize financial years.
    # ------------------------------------------------------------------

    if "year" in result.columns:
        result["year"] = result[
            "year"
        ].apply(
            normalize_year
        )

    # ------------------------------------------------------------------
    # Documents:
    #
    # id -> document_id
    # ------------------------------------------------------------------

    if table_name in SOURCE_COLUMN_RENAMES:

        rename_mapping = SOURCE_COLUMN_RENAMES[
            table_name
        ]

        result = result.rename(
            columns=rename_mapping
        )

    # ------------------------------------------------------------------
    # Financial ratios:
    #
    # descriptive source names -> ratio_1 ... ratio_13
    # ------------------------------------------------------------------

    if table_name == "financial_ratios":

        result = result.rename(
            columns=FINANCIAL_RATIO_RENAMES
        )

    # ------------------------------------------------------------------
    # Stock price date.
    # ------------------------------------------------------------------

    if (
        table_name == "stock_prices"
        and "price_date" in result.columns
    ):
        result["price_date"] = result[
            "price_date"
        ].apply(
            normalize_price_date
        )

    # ------------------------------------------------------------------
    # Remove source-only ID columns.
    #
    # Documents is the exception because its source "id" has already
    # been converted into the database's document_id.
    # ------------------------------------------------------------------

    if (
        table_name not in {
            "companies",
            "documents",
        }
        and "id" in result.columns
    ):
        result = result.drop(
            columns=["id"]
        )

    # ------------------------------------------------------------------
    # Convert pandas NaN/NA to Python None.
    # ------------------------------------------------------------------

    result = result.astype(
        object
    ).where(
        pd.notna(result),
        None,
    )

    return result


# ============================================================================
# DATABASE SCHEMA HELPERS
# ============================================================================


def get_database_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[str]:
    """
    Return columns defined by the SQLite table.
    """

    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    if not rows:
        raise RuntimeError(
            f"Database table '{table_name}' does not exist."
        )

    return [
        row[1]
        for row in rows
    ]


def align_dataframe_to_database(
    df: pd.DataFrame,
    table_name: str,
    connection: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Align DataFrame columns to the actual SQLite schema.

    Important:
    document_id is NOT generated by SQLite in the current schema because
    it is defined as INTEGER PRIMARY KEY rather than INTEGER PRIMARY KEY
    AUTOINCREMENT. Therefore documents.xlsx must supply document_id.

    Extra source columns are safely ignored after validation.
    """

    database_columns = get_database_columns(
        connection,
        table_name,
    )

    source_columns = list(
        df.columns
    )

    missing_columns = [
        column
        for column in database_columns
        if column not in source_columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name}: source data is missing required "
            f"database columns: {missing_columns}\n"
            f"Source columns: {source_columns}\n"
            f"Database columns: {database_columns}"
        )

    # Ignore source columns not present in the database schema.
    extra_columns = [
        column
        for column in source_columns
        if column not in database_columns
    ]

    if extra_columns:
        df = df.drop(
            columns=extra_columns
        )

    # Return columns in exactly the same order as SQLite schema.
    return df[
        database_columns
    ].copy()


# ============================================================================
# DATA QUALITY TRANSFORMATIONS
# ============================================================================


def reject_invalid_year_rows(
    df: pd.DataFrame,
    table_name: str,
) -> tuple[pd.DataFrame, int]:
    """
    Remove rows whose normalized year is NULL.
    """

    if "year" not in df.columns:
        return df, 0

    invalid_mask = df[
        "year"
    ].isna()

    rejected = int(
        invalid_mask.sum()
    )

    if rejected > 0:
        print(
            f"  Warning: {table_name} contains "
            f"{rejected} rows with invalid/non-annual "
            f"year values."
        )

    return (
        df.loc[
            ~invalid_mask
        ].copy(),
        rejected,
    )


def filter_master_company_universe(
    df: pd.DataFrame,
    master_company_ids: set[str],
    table_name: str,
) -> tuple[pd.DataFrame, int]:
    """
    Keep only records belonging to companies in the master companies table.
    """

    if table_name == "companies":
        return df, 0

    if "company_id" not in df.columns:
        return df, 0

    valid_mask = df[
        "company_id"
    ].isin(
        master_company_ids
    )

    rejected = len(df) - int(
        valid_mask.sum()
    )

    if rejected > 0:

        invalid_ids = sorted(
            set(
                df.loc[
                    ~valid_mask,
                    "company_id",
                ]
                .dropna()
                .astype(str)
            )
        )

        print(
            f"  Warning: {table_name} contains "
            f"{rejected} rows belonging to companies "
            f"outside the {len(master_company_ids)}-company "
            f"master universe."
        )

        if invalid_ids:
            print(
                "  Excluded company IDs: "
                + ", ".join(
                    invalid_ids
                )
            )

    return (
        df.loc[
            valid_mask
        ].copy(),
        rejected,
    )


def deduplicate_dataframe(
    df: pd.DataFrame,
    table_name: str,
) -> tuple[pd.DataFrame, int]:
    """
    Remove duplicate logical records.
    """

    if df.empty:
        return df, 0

    # --------------------------------------------------------------
    # Company-year tables.
    # --------------------------------------------------------------

    if table_name in TIME_SERIES_TABLES:

        key_columns = [
            "company_id",
            "year",
        ]

    # --------------------------------------------------------------
    # Company snapshot tables.
    # --------------------------------------------------------------

    elif table_name in COMPANY_SNAPSHOT_TABLES:

        key_columns = [
            "company_id"
        ]

    # --------------------------------------------------------------
    # Stock prices.
    # --------------------------------------------------------------

    elif table_name == "stock_prices":

        key_columns = [
            "company_id",
            "price_date",
        ]

    # --------------------------------------------------------------
    # Documents:
    #
    # document_id is already unique in the source.
    # Do not incorrectly deduplicate by company/year because one company
    # can legitimately have multiple documents.
    # --------------------------------------------------------------

    elif table_name == "documents":

        key_columns = [
            "document_id"
        ]

    else:
        key_columns = []

    if not key_columns:
        return df, 0

    existing_keys = [
        column
        for column in key_columns
        if column in df.columns
    ]

    if len(existing_keys) != len(
        key_columns
    ):
        return df, 0

    duplicate_mask = df.duplicated(
        subset=key_columns,
        keep="first",
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    if duplicate_count > 0:

        print(
            f"  Warning: {table_name} contains "
            f"{duplicate_count} duplicate rows "
            f"for constraint "
            f"({', '.join(key_columns)})."
        )

        print(
            "  Keeping the first occurrence "
            "for each logical key."
        )

    return (
        df.loc[
            ~duplicate_mask
        ].copy(),
        duplicate_count,
    )


# ============================================================================
# VALIDATION
# ============================================================================


def validate_required_fields(
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """
    Validate required NOT NULL fields before insertion.
    """

    if df.empty:
        return

    # --------------------------------------------------------------
    # Companies.
    # --------------------------------------------------------------

    if table_name == "companies":

        if "company_id" not in df.columns:
            raise ValueError(
                "companies: required column "
                "'company_id' is missing."
            )

        null_count = int(
            df[
                "company_id"
            ].isna().sum()
        )

        if null_count:
            raise ValueError(
                f"companies: {null_count} rows "
                "contain NULL company_id."
            )

        return

    # --------------------------------------------------------------
    # Every child table requires company_id.
    # --------------------------------------------------------------

    if "company_id" not in df.columns:
        raise ValueError(
            f"{table_name}: required column "
            "'company_id' is missing."
        )

    null_company_count = int(
        df[
            "company_id"
        ].isna().sum()
    )

    if null_company_count:
        raise ValueError(
            f"{table_name}: {null_company_count} rows "
            "contain NULL company_id."
        )

    # --------------------------------------------------------------
    # Time-series tables require year.
    # --------------------------------------------------------------

    if table_name in TIME_SERIES_TABLES:

        if "year" not in df.columns:
            raise ValueError(
                f"{table_name}: required column "
                "'year' is missing."
            )

        null_year_count = int(
            df[
                "year"
            ].isna().sum()
        )

        if null_year_count:
            raise ValueError(
                f"{table_name}: {null_year_count} rows "
                "contain NULL year."
            )

    # --------------------------------------------------------------
    # Stock prices require price_date.
    # --------------------------------------------------------------

    if table_name == "stock_prices":

        if "price_date" not in df.columns:
            raise ValueError(
                "stock_prices: required column "
                "'price_date' is missing."
            )

        null_date_count = int(
            df[
                "price_date"
            ].isna().sum()
        )

        if null_date_count:
            raise ValueError(
                f"stock_prices: {null_date_count} rows "
                "contain NULL price_date."
            )

    # --------------------------------------------------------------
    # Documents require document_id.
    # --------------------------------------------------------------

    if table_name == "documents":

        if "document_id" not in df.columns:
            raise ValueError(
                "documents: required column "
                "'document_id' is missing. "
                "The loader expects documents.xlsx 'id' "
                "to be mapped to document_id."
            )

        null_document_count = int(
            df[
                "document_id"
            ].isna().sum()
        )

        if null_document_count:
            raise ValueError(
                f"documents: {null_document_count} rows "
                "contain NULL document_id."
            )


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================


def clear_existing_records(
    connection: sqlite3.Connection,
) -> None:
    """
    Delete existing records from all loader-managed tables.

    Child tables are deleted before the parent companies table.
    """

    deletion_order = [
        "financial_ratios",
        "stock_prices",
        "sectors",
        "prosandcons",
        "documents",
        "analysis",
        "cashflow",
        "balancesheet",
        "profitandloss",
        "companies",
    ]

    for table_name in deletion_order:

        try:

            connection.execute(
                f"DELETE FROM {table_name}"
            )

        except sqlite3.OperationalError as exc:

            if "no such table" in str(
                exc
            ).lower():

                raise RuntimeError(
                    f"Database table '{table_name}' "
                    "does not exist. "
                    "Create the database schema before "
                    "running the loader."
                ) from exc

            raise


def load_dataframe_to_database(
    connection: sqlite3.Connection,
    df: pd.DataFrame,
    table_name: str,
) -> int:
    """
    Insert DataFrame into SQLite.
    """

    if df.empty:
        return 0

    validate_required_fields(
        df,
        table_name,
    )

    df.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
    )

    return len(df)


# ============================================================================
# LOAD COMPANIES
# ============================================================================


def load_companies(
    connection: sqlite3.Connection,
) -> tuple[set[str], int]:
    """
    Load companies and return the master company universe.
    """

    print(
        "Loading companies.xlsx..."
    )

    raw_df = load_source_file(
        "companies.xlsx"
    )

    df = prepare_dataframe(
        raw_df,
        "companies",
    )

    if "company_id" not in df.columns:
        raise ValueError(
            "companies.xlsx does not contain "
            "'id' or 'company_id'."
        )

    # Remove NULL company IDs.
    df = df.dropna(
        subset=["company_id"]
    )

    # Remove duplicate company IDs.
    duplicate_mask = df.duplicated(
        subset=["company_id"],
        keep="first",
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    if duplicate_count > 0:

        print(
            f"  Warning: companies contains "
            f"{duplicate_count} duplicate company IDs."
        )

        print(
            "  Keeping the first occurrence."
        )

        df = df.loc[
            ~duplicate_mask
        ].copy()

    if df.empty:
        raise ValueError(
            "companies.xlsx produced zero valid companies."
        )

    df = align_dataframe_to_database(
        df,
        "companies",
        connection,
    )

    validate_required_fields(
        df,
        "companies",
    )

    inserted = load_dataframe_to_database(
        connection,
        df,
        "companies",
    )

    master_company_ids = set(
        df[
            "company_id"
        ].astype(str)
    )

    print(
        f"  -> {inserted} rows inserted into companies"
    )

    print()
    print(
        f"Master company universe: "
        f"{len(master_company_ids)} companies"
    )

    return (
        master_company_ids,
        inserted,
    )


# ============================================================================
# PROCESS ONE SOURCE
# ============================================================================


def process_source(
    connection: sqlite3.Connection,
    filename: str,
    master_company_ids: set[str],
) -> tuple[int, dict[str, int]]:
    """
    Process one child source file.
    """

    table_name = SOURCE_TO_TABLE[
        filename
    ]

    print()
    print(
        f"Loading {filename}..."
    )

    # --------------------------------------------------------------
    # READ
    # --------------------------------------------------------------

    raw_df = load_source_file(
        filename
    )

    rows_in = len(
        raw_df
    )

    # --------------------------------------------------------------
    # NORMALIZE + SOURCE-SPECIFIC MAPPING
    # --------------------------------------------------------------

    df = prepare_dataframe(
        raw_df,
        table_name,
    )

    # --------------------------------------------------------------
    # INVALID YEAR
    # --------------------------------------------------------------

    df, rejected_invalid_year = (
        reject_invalid_year_rows(
            df,
            table_name,
        )
    )

    # --------------------------------------------------------------
    # MASTER COMPANY FILTER
    # --------------------------------------------------------------

    df, rejected_invalid_company = (
        filter_master_company_universe(
            df,
            master_company_ids,
            table_name,
        )
    )

    # --------------------------------------------------------------
    # REMOVE NULL COMPANY IDS
    # --------------------------------------------------------------

    if "company_id" in df.columns:

        null_company_mask = df[
            "company_id"
        ].isna()

        null_company_count = int(
            null_company_mask.sum()
        )

        if null_company_count > 0:

            print(
                f"  Warning: {table_name} contains "
                f"{null_company_count} rows without "
                "company_id."
            )

            df = df.loc[
                ~null_company_mask
            ].copy()

            rejected_invalid_company += (
                null_company_count
            )

    # --------------------------------------------------------------
    # REMOVE NULL STOCK DATES
    # --------------------------------------------------------------

    if table_name == "stock_prices":

        invalid_date_mask = df[
            "price_date"
        ].isna()

        invalid_date_count = int(
            invalid_date_mask.sum()
        )

        if invalid_date_count > 0:

            print(
                f"  Warning: stock_prices contains "
                f"{invalid_date_count} invalid dates."
            )

            df = df.loc[
                ~invalid_date_mask
            ].copy()

    # --------------------------------------------------------------
    # DEDUPLICATE
    # --------------------------------------------------------------

    df, rejected_duplicates = (
        deduplicate_dataframe(
            df,
            table_name,
        )
    )

    # --------------------------------------------------------------
    # ALIGN WITH DATABASE SCHEMA
    # --------------------------------------------------------------

    df = align_dataframe_to_database(
        df,
        table_name,
        connection,
    )

    # --------------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------------

    validate_required_fields(
        df,
        table_name,
    )

    # --------------------------------------------------------------
    # INSERT
    # --------------------------------------------------------------

    inserted = load_dataframe_to_database(
        connection,
        df,
        table_name,
    )

    rejected_total = (
        rejected_invalid_year
        + rejected_invalid_company
        + rejected_duplicates
    )

    print(
        f"  -> {inserted} rows inserted into "
        f"{table_name}"
    )

    audit = {
        "rows_in": rows_in,
        "rows_out": inserted,
        "rejected_invalid_year": (
            rejected_invalid_year
        ),
        "rejected_invalid_company": (
            rejected_invalid_company
        ),
        "rejected_duplicates": (
            rejected_duplicates
        ),
        "rejected_total": rejected_total,
    }

    return (
        inserted,
        audit,
    )


# ============================================================================
# FINAL INTEGRITY CHECKS
# ============================================================================


def run_final_integrity_checks(
    connection: sqlite3.Connection,
    master_company_ids: set[str],
) -> None:
    """
    Run final database integrity checks before commit.
    """

    print()
    print(
        "Running final database integrity checks..."
    )

    # --------------------------------------------------------------
    # Foreign keys.
    # --------------------------------------------------------------

    foreign_key_violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if foreign_key_violations:

        raise RuntimeError(
            "Foreign-key integrity check failed: "
            f"{foreign_key_violations[:10]}"
        )

    print(
        "  [OK] Foreign-key integrity"
    )

    # --------------------------------------------------------------
    # Companies count.
    # --------------------------------------------------------------

    company_count = connection.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    if company_count != len(
        master_company_ids
    ):

        raise RuntimeError(
            "Companies count mismatch: "
            f"database={company_count}, "
            f"master={len(master_company_ids)}"
        )

    print(
        f"  [OK] Companies: {company_count}"
    )

    # --------------------------------------------------------------
    # Time-series tables.
    # --------------------------------------------------------------

    for table_name in TIME_SERIES_TABLES:

        null_year_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE year IS NULL
            """
        ).fetchone()[0]

        if null_year_count != 0:

            raise RuntimeError(
                f"{table_name} contains "
                f"{null_year_count} NULL year values."
            )

        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT company_id, year
                FROM {table_name}
                GROUP BY company_id, year
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if duplicate_count != 0:

            raise RuntimeError(
                f"{table_name} contains "
                f"{duplicate_count} duplicate "
                "(company_id, year) keys."
            )

        print(
            f"  [OK] {table_name}: "
            "valid annual company-year keys"
        )

    # --------------------------------------------------------------
    # Analysis uniqueness.
    # --------------------------------------------------------------

    analysis_duplicates = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT company_id
            FROM analysis
            GROUP BY company_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if analysis_duplicates != 0:

        raise RuntimeError(
            "analysis contains duplicate company_id values."
        )

    print(
        "  [OK] analysis: unique company_id"
    )

    # --------------------------------------------------------------
    # Sectors uniqueness.
    # --------------------------------------------------------------

    sectors_duplicates = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT company_id
            FROM sectors
            GROUP BY company_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if sectors_duplicates != 0:

        raise RuntimeError(
            "sectors contains duplicate company_id values."
        )

    print(
        "  [OK] sectors: unique company_id"
    )

    # --------------------------------------------------------------
    # Pros and cons uniqueness.
    # --------------------------------------------------------------

    prosandcons_duplicates = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT company_id
            FROM prosandcons
            GROUP BY company_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if prosandcons_duplicates != 0:

        raise RuntimeError(
            "prosandcons contains duplicate company_id values."
        )

    print(
        "  [OK] prosandcons: unique company_id"
    )

    # --------------------------------------------------------------
    # Stock-price uniqueness.
    # --------------------------------------------------------------

    stock_price_duplicates = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT company_id, price_date
            FROM stock_prices
            GROUP BY company_id, price_date
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if stock_price_duplicates != 0:

        raise RuntimeError(
            "stock_prices contains duplicate "
            "(company_id, price_date) keys."
        )

    print(
        "  [OK] stock_prices: unique company-date keys"
    )

    # --------------------------------------------------------------
    # Documents uniqueness.
    # --------------------------------------------------------------

    document_duplicates = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT document_id
            FROM documents
            GROUP BY document_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if document_duplicates != 0:

        raise RuntimeError(
            "documents contains duplicate document_id values."
        )

    print(
        "  [OK] documents: unique document_id"
    )

    print(
        "Final integrity checks passed."
    )


# ============================================================================
# FULL LOAD
# ============================================================================


def load_all_sources() -> dict[str, int]:
    """
    Load the complete database transactionally.

    If any table fails, every change is rolled back.
    """

    results: dict[str, int] = {}

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        # ----------------------------------------------------------
        # Enable foreign keys.
        # ----------------------------------------------------------

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if foreign_keys_enabled != 1:

            raise RuntimeError(
                "SQLite foreign-key enforcement "
                "could not be enabled."
            )

        # ----------------------------------------------------------
        # Clear old records.
        # ----------------------------------------------------------

        print()
        print(
            "Clearing existing database records..."
        )

        clear_existing_records(
            connection
        )

        print(
            "Existing records cleared."
        )

        # ----------------------------------------------------------
        # Load companies first.
        # ----------------------------------------------------------

        (
            master_company_ids,
            company_count,
        ) = load_companies(
            connection
        )

        results[
            "companies"
        ] = company_count

        # ----------------------------------------------------------
        # Load all child tables.
        # ----------------------------------------------------------

        audit_results: dict[
            str,
            dict[str, int],
        ] = {}

        for filename in ORDERED_SOURCES:

            if filename == "companies.xlsx":
                continue

            table_name = SOURCE_TO_TABLE[
                filename
            ]

            (
                inserted,
                audit,
            ) = process_source(
                connection=connection,
                filename=filename,
                master_company_ids=master_company_ids,
            )

            results[
                table_name
            ] = inserted

            audit_results[
                table_name
            ] = audit

        # ----------------------------------------------------------
        # Final validation.
        # ----------------------------------------------------------

        run_final_integrity_checks(
            connection,
            master_company_ids,
        )

        # ----------------------------------------------------------
        # Commit ONLY after everything passes.
        # ----------------------------------------------------------

        connection.commit()

        print()
        print(
            "=" * 70
        )
        print(
            "DATABASE LOAD: PASSED"
        )
        print(
            "=" * 70
        )

    except Exception:

        connection.rollback()

        print()
        print(
            "=" * 70
        )
        print(
            "DATABASE LOAD FAILED."
        )
        print(
            "All changes have been rolled back."
        )
        print(
            "=" * 70
        )

        raise

    finally:

        connection.close()

    return results


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """
    Run complete database loading process.
    """

    print(
        "=" * 70
    )

    print(
        "NIFTY 100 DATABASE LOADER"
    )

    print(
        "=" * 70
    )

    print(
        f"Database: {DATABASE_PATH}"
    )

    print(
        f"Source directory: {RAW_DIR}"
    )

    print(
        f"Supporting directory: {SUPPORTING_DIR}"
    )

    print()

    results = load_all_sources()

    print()
    print(
        "-" * 70
    )

    print(
        "ROWS INSERTED"
    )

    print(
        "-" * 70
    )

    total = 0

    for table_name, row_count in results.items():

        print(
            f"{table_name:<25} "
            f"{row_count:>6} rows"
        )

        total += row_count

    print(
        "-" * 70
    )

    print(
        f"Total rows inserted: {total}"
    )

    print(
        "=" * 70
    )

    print(
        "DATABASE LOAD: PASSED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()