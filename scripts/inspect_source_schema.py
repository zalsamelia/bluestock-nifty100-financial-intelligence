"""
Inspect the structure of all source Excel files.

This script prints:
- file name
- column names
- number of rows
- sample records
"""

from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


SOURCE_FILES = [
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
    "market_cap.xlsx",
    "peer_groups.xlsx",
]


def inspect_file(file_path: Path) -> None:
    """Print structural information for one Excel file."""

    print("\n" + "=" * 70)
    print(f"FILE: {file_path.name}")
    print("=" * 70)

    try:
        df = pd.read_excel(file_path, header=1)

        print(f"Rows    : {len(df)}")
        print(f"Columns : {len(df.columns)}")

        print("\nColumn names:")
        for column in df.columns:
            print(f"  - {column}")

        print("\nFirst 3 rows:")
        print(df.head(3).to_string(index=False))

    except Exception as exc:
        print(f"ERROR: {exc}")


def main() -> None:
    """Inspect all configured source files."""

    print("=" * 70)
    print("SOURCE SCHEMA INSPECTION")
    print("=" * 70)

    for filename in SOURCE_FILES:
        file_path = RAW_DIR / filename

        if not file_path.exists():
            print(f"\nWARNING: Missing file: {file_path}")
            continue

        inspect_file(file_path)

    print("\n" + "=" * 70)
    print("SCHEMA INSPECTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()