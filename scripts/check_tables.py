import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")


def main():
    print("=" * 70)
    print("NIFTY 100 DATABASE TABLE CHECK")
    print("=" * 70)

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print("\nTables found:")
    print("-" * 70)

    for (table_name,) in tables:
        print(table_name)

    print("\nTable count:", len(tables))

    conn.close()


if __name__ == "__main__":
    main()