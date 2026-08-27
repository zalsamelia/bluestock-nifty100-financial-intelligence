from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


def main() -> None:
    files = sorted(RAW_DIR.glob("*.xlsx"))

    if not files:
        print("No Excel files found in data/raw/")
        return

    print("=" * 60)
    print("SOURCE FILE ROW COUNT")
    print("=" * 60)

    for file in files:
        try:
            df = pd.read_excel(file, header=1)

            print(f"{file.name:<25} {len(df):>6} rows")

        except Exception as exc:
            print(f"{file.name:<25} ERROR: {exc}")

    print("=" * 60)
    print(f"Total files found: {len(files)}")


if __name__ == "__main__":
    main()