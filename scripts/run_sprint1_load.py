"""
Sprint 1 load wrapper.

Runs the existing, already-passing database loader and captures its
wall-clock runtime so load_audit.csv contains the required runtime field.

This script does not replace database_loader.py.
"""

from __future__ import annotations

import csv
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "nifty100.db"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

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


def raw_rows(path: Path) -> int:
    df = pd.read_excel(path, header=1)
    return int(len(df.dropna(axis=0, how="all")))


def db_rows() -> dict[str, int]:
    import sqlite3

    with sqlite3.connect(DB_PATH) as conn:
        result = {}
        for table in SOURCE_TO_TABLE.values():
            result[table] = int(
                conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            )
    return result


def main() -> None:
    start = time.perf_counter()

    completed = False
    process = subprocess.run(
        [sys.executable, "-m", "src.etl.database_loader"],
        cwd=PROJECT_ROOT,
        check=False,
    )

    runtime = round(time.perf_counter() - start, 3)

    if process.returncode != 0:
        raise SystemExit(process.returncode)

    counts = db_rows()
    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []
    for filename, table in SOURCE_TO_TABLE.items():
        source = RAW_DIR / filename
        rows_in = raw_rows(source)
        rows_out = counts[table]
        rows.append(
            {
                "table": table,
                "rows_in": rows_in,
                "rows_out": rows_out,
                "rejected": max(rows_in - rows_out, 0),
                "timestamp": timestamp,
                "runtime_s": runtime,
            }
        )

    OUTPUT_DIR = PROJECT_ROOT / "output"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = REPORT_DIR / "load_audit.csv"
    output_dir_file = OUTPUT_DIR / "load_audit.csv"

    pd.DataFrame(rows).to_csv(output, index=False)
    pd.DataFrame(rows).to_csv(output_dir_file, index=False)

    print()
    print("=" * 70)
    print("LOAD AUDIT CREATED")
    print("=" * 70)
    print(f"File: {output}")
    print(f"File: {output_dir_file}")
    print(f"Runtime: {runtime:.3f}s")
    print()
    print(pd.DataFrame(rows).to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
