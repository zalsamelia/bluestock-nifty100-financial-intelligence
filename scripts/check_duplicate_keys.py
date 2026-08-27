from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

FILES = {
    "profitandloss.xlsx": ["company_id", "year"],
    "balancesheet.xlsx": ["company_id", "year"],
    "cashflow.xlsx": ["company_id", "year"],
    "financial_ratios.xlsx": ["company_id", "year"],
}


def check_duplicates(filename: str, key_columns: list[str]) -> None:
    path = RAW_DIR / filename

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    if not path.exists():
        print(f"FILE NOT FOUND: {path}")
        return

    df = pd.read_excel(path, header=1)

    print(f"Total rows: {len(df)}")

    missing_columns = [
        column for column in key_columns
        if column not in df.columns
    ]

    if missing_columns:
        print(f"Missing columns: {missing_columns}")
        return

    duplicate_mask = df.duplicated(
        subset=key_columns,
        keep=False,
    )

    duplicate_rows = df.loc[duplicate_mask].copy()

    if duplicate_rows.empty:
        print("Duplicate key rows: 0")
        print("STATUS: PASS")
        return

    duplicate_groups = (
        duplicate_rows
        .groupby(key_columns, dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    print(f"Duplicate key rows: {len(duplicate_rows)}")
    print(f"Duplicate key groups: {len(duplicate_groups)}")

    print("\nDuplicate key groups:")
    print(duplicate_groups.to_string(index=False))

    print("\nDuplicate rows:")
    print(duplicate_rows.to_string(index=False))

    print("\nSTATUS: DUPLICATES FOUND")


def main() -> None:
    print("=" * 70)
    print("NIFTY 100 DUPLICATE KEY CHECK")
    print("=" * 70)
    print(f"Raw directory: {RAW_DIR}")

    for filename, key_columns in FILES.items():
        check_duplicates(filename, key_columns)

    print("\n" + "=" * 70)
    print("DUPLICATE KEY CHECK COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()