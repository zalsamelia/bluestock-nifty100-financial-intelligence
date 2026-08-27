import sys
from pathlib import Path

import pandas as pd


# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.normaliser import normalize_dataframe


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


def main():
    print("=" * 70)
    print("NORMALIZATION TEST ON SOURCE FILES")
    print("=" * 70)

    for filename in SOURCE_FILES:
        path = RAW_DIR / filename

        print(f"\n{'=' * 70}")
        print(filename)
        print("=" * 70)

        if not path.exists():
            print("FILE NOT FOUND")
            continue

        df = pd.read_excel(path, header=1)

        print(f"Raw shape: {df.shape}")
        print(f"Columns before normalization:")
        print(list(df.columns))

        normalized = normalize_dataframe(df)

        print(f"\nNormalized shape: {normalized.shape}")
        print("Columns after normalization:")
        print(list(normalized.columns))

        print("\nFirst 3 rows:")
        print(normalized.head(3).to_string(index=False))


if __name__ == "__main__":
    main()