"""
Database structure validation script.

Checks:
- SQLite database creation
- Expected table names
- Table row counts
- Foreign key enforcement
- Foreign key violations
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")

EXPECTED_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "financial_ratios",
]


def main():
    print("=" * 70)
    print("NIFTY100 DATABASE CHECK")
    print("=" * 70)

    if not DB_PATH.exists():
        print("ERROR: nifty100.db does not exist.")
        return

    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)

    try:
        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON")

        foreign_keys = conn.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        print(f"Foreign key enforcement: {foreign_keys}")
        print()

        # Get existing tables
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        existing_tables = [row[0] for row in rows]

        print("Tables found:")
        print("-" * 70)

        for table in existing_tables:
            count = conn.execute(
                f"SELECT COUNT(*) FROM [{table}]"
            ).fetchone()[0]

            print(f"{table:<25} {count:>8} rows")

        print()

        # Check expected tables
        missing_tables = [
            table
            for table in EXPECTED_TABLES
            if table not in existing_tables
        ]

        unexpected_tables = [
            table
            for table in existing_tables
            if table not in EXPECTED_TABLES
        ]

        print("Expected table check:")
        print("-" * 70)

        if not missing_tables:
            print("All expected tables are present.")
        else:
            print("Missing tables:")
            for table in missing_tables:
                print(f"  - {table}")

        if unexpected_tables:
            print()
            print("Additional tables found:")
            for table in unexpected_tables:
                print(f"  - {table}")

        print()

        # Foreign key validation
        violations = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("Foreign key check:")
        print("-" * 70)

        if not violations:
            print("Foreign key violations: 0")
        else:
            print(f"Foreign key violations: {len(violations)}")
            for violation in violations:
                print(violation)

        print()

        # Final status
        print("=" * 70)

        if missing_tables:
            print("DATABASE CHECK: FAILED")
        elif foreign_keys != 1:
            print("DATABASE CHECK: FAILED")
        elif violations:
            print("DATABASE CHECK: FAILED")
        else:
            print("DATABASE CHECK: PASSED")

        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()