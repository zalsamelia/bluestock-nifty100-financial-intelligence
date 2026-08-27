"""
Manual test for Sprint 1 data quality validation.

This script can be executed directly from the project root:

    python scripts/test_dq_rules.py
"""

from pathlib import Path
import sys

# ---------------------------------------------------------------------
# Ensure the project root is available on Python's import path.
# This allows:
#     python scripts/test_dq_rules.py
# to import modules from src/.
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import pandas as pd

from src.etl.validator import DataValidator


RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"


SOURCE_FILES = {
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
}


def load_sources() -> dict[str, pd.DataFrame]:
    """
    Load all core Excel source files.

    Returns:
        Dictionary mapping table names to DataFrames.
    """

    datasets: dict[str, pd.DataFrame] = {}

    for table_name, filename in SOURCE_FILES.items():
        path = RAW_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Source file not found: {path}"
            )

        datasets[table_name] = pd.read_excel(
            path,
            header=1,
        )

    return datasets


def test_validator_initialization() -> None:
    """Test that DataValidator initializes without failures."""

    validator = DataValidator()

    assert validator.failures == []

    failures = validator.get_failures()

    assert failures.empty

    print("[PASS] Validator initialization")


def test_add_failure() -> None:
    """Test that a validation failure can be recorded."""

    validator = DataValidator()

    validator.add_failure(
        rule_id="DQ-TEST",
        severity="WARNING",
        table="test_table",
        message="Test validation failure",
        row_count=1,
    )

    failures = validator.get_failures()

    assert len(failures) == 1
    assert failures.iloc[0]["rule_id"] == "DQ-TEST"
    assert failures.iloc[0]["severity"] == "WARNING"
    assert failures.iloc[0]["table"] == "test_table"
    assert failures.iloc[0]["row_count"] == 1

    print("[PASS] Failure recording")


def test_save_failures() -> None:
    """Test that validation failures can be written to CSV."""

    validator = DataValidator()

    validator.add_failure(
        rule_id="DQ-TEST",
        severity="WARNING",
        table="test_table",
        message="Test CSV output",
        row_count=1,
    )

    test_output = OUTPUT_DIR / "test_validation_failures.csv"

    validator.save_failures(test_output)

    assert test_output.exists()

    result = pd.read_csv(test_output)

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-TEST"

    test_output.unlink()

    print("[PASS] Failure CSV output")


def inspect_source_files(
    datasets: dict[str, pd.DataFrame],
) -> None:
    """Print basic information about all source datasets."""

    print()
    print("=" * 70)
    print("SOURCE DATA INSPECTION")
    print("=" * 70)

    for table_name, df in datasets.items():
        print(
            f"{table_name:<20} "
            f"{len(df):>6} rows × "
            f"{len(df.columns):>2} columns"
        )


def main() -> None:
    """Run the validator smoke tests and inspect source datasets."""

    print("=" * 70)
    print("NIFTY 100 DATA QUALITY VALIDATOR TEST")
    print("=" * 70)

    test_validator_initialization()
    test_add_failure()
    test_save_failures()

    datasets = load_sources()

    inspect_source_files(datasets)

    print()
    print("=" * 70)
    print("VALIDATOR TESTS: PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()