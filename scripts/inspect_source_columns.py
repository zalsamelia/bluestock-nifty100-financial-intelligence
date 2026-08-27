"""Inspect columns and sample records from all source Excel files."""

from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


def main() -> None:
    """Print source file columns and sample records."""

    files = sorted(RAW_DIR.glob("*.xlsx"))

    print("=" * 70)
    print("SOURCE COLUMN INSPECTION")
    print("=" * 70)

    for file in files:
        print()
        print(f"FILE: {file.name}")
        print("-" * 70)

        df = pd.read_excel(file, header=1)

        print("Columns:")
        for column in df.columns:
            print(f"  - {column}")

        print()
        print("Sample:")
        print(df.head(2).to_string(index=False))


if __name__ == "__main__":
    main()