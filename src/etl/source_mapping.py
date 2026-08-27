"""
Source-to-table mapping for the Nifty 100 ETL pipeline.

The project contains 12 Excel source files, while the Sprint 1
database schema contains 10 target tables.

Two supplementary source files are retained in data/raw but are
not loaded into the Sprint 1 SQLite schema.
"""

from pathlib import Path


RAW_DIR = Path("data/raw")


SOURCE_MAPPING = {
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
    "market_cap.xlsx": None,
    "peer_groups.xlsx": None,
}


def main():
    print("=" * 70)
    print("NIFTY 100 SOURCE MAPPING")
    print("=" * 70)

    for filename, table_name in SOURCE_MAPPING.items():
        if table_name is None:
            print(f"{filename:<28} -> SUPPLEMENTARY / NOT LOADED")
        else:
            print(f"{filename:<28} -> {table_name}")


if __name__ == "__main__":
    main()