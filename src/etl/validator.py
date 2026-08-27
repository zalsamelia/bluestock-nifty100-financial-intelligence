"""
Data quality validation module for NIFTY 100 financial data.

This module implements validation rules DQ-01 to DQ-16
defined in Sprint 1 of the NIFTY 100 Financial Intelligence project.
"""

from pathlib import Path
from typing import Any

import pandas as pd


class ValidationFailure:
    """Represent a single data quality validation failure."""

    def __init__(
        self,
        rule_id: str,
        severity: str,
        table: str,
        message: str,
        row_count: int = 0,
    ) -> None:
        self.rule_id = rule_id
        self.severity = severity
        self.table = table
        self.message = message
        self.row_count = row_count

    def to_dict(self) -> dict[str, Any]:
        """Convert validation failure to dictionary format."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "table": self.table,
            "message": self.message,
            "row_count": self.row_count,
        }


class DataValidator:
    """Run data quality checks against source datasets."""

    def __init__(self) -> None:
        self.failures: list[ValidationFailure] = []

    def add_failure(
        self,
        rule_id: str,
        severity: str,
        table: str,
        message: str,
        row_count: int = 0,
    ) -> None:
        """Record a validation failure."""
        self.failures.append(
            ValidationFailure(
                rule_id=rule_id,
                severity=severity,
                table=table,
                message=message,
                row_count=row_count,
            )
        )

    def get_failures(self) -> pd.DataFrame:
        """Return all validation failures as a DataFrame."""
        if not self.failures:
            return pd.DataFrame(
                columns=[
                    "rule_id",
                    "severity",
                    "table",
                    "message",
                    "row_count",
                ]
            )

        return pd.DataFrame(
            [failure.to_dict() for failure in self.failures]
        )

    def save_failures(self, output_path: str | Path) -> None:
        """Save validation failures to CSV."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.get_failures().to_csv(
            output_path,
            index=False,
        )

    def check_primary_key_uniqueness(
        self,
        df: pd.DataFrame,
        table: str,
        columns: list[str],
        rule_id: str = "DQ-01",
    ) -> None:
        """
        Check whether the specified columns form a unique primary key.

        A CRITICAL failure is recorded when duplicate keys are found.
        """

        if not all(column in df.columns for column in columns):
            missing = [
                column
                for column in columns
                if column not in df.columns
            ]

            self.add_failure(
                rule_id=rule_id,
                severity="CRITICAL",
                table=table,
                message=(
                    f"Required key columns are missing: {missing}"
                ),
            )
            return

        duplicate_mask = df.duplicated(
            subset=columns,
            keep=False,
        )

        duplicate_count = int(duplicate_mask.sum())

        if duplicate_count > 0:
            self.add_failure(
                rule_id=rule_id,
                severity="CRITICAL",
                table=table,
                message=(
                    f"Duplicate primary-key values detected "
                    f"using columns {columns}."
                ),
                row_count=duplicate_count,
            )

    def check_company_year_uniqueness(
        self,
        df: pd.DataFrame,
        table: str,
    ) -> None:
        """
        Check uniqueness of the (company_id, year) composite key.

        Used for financial tables where each company should have
        at most one record for each financial year.
        """

        self.check_primary_key_uniqueness(
            df=df,
            table=table,
            columns=["company_id", "year"],
            rule_id="DQ-02",
        )

    def check_foreign_key_integrity(
        self,
        child_df: pd.DataFrame,
        parent_df: pd.DataFrame,
        child_table: str,
        child_column: str = "company_id",
        parent_column: str = "company_id",
    ) -> None:
        """
        Check whether child-table foreign keys exist in the parent table.

        The companies table acts as the parent table for company-related
        datasets.
        """

        if child_column not in child_df.columns:
            self.add_failure(
                rule_id="DQ-03",
                severity="CRITICAL",
                table=child_table,
                message=(
                    f"Foreign-key column '{child_column}' "
                    f"is missing."
                ),
            )
            return

        if parent_column not in parent_df.columns:
            self.add_failure(
                rule_id="DQ-03",
                severity="CRITICAL",
                table="companies",
                message=(
                    f"Parent key column '{parent_column}' "
                    f"is missing."
                ),
            )
            return

        parent_keys = set(
            parent_df[parent_column]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
        )

        child_keys = (
            child_df[child_column]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        invalid_mask = ~child_keys.isin(parent_keys)

        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            self.add_failure(
                rule_id="DQ-03",
                severity="CRITICAL",
                table=child_table,
                message=(
                    f"{invalid_count} foreign-key values in "
                    f"'{child_column}' do not exist in companies."
                ),
                row_count=invalid_count,
            )

    def check_balance_sheet_balance(
        self,
        df: pd.DataFrame,
        table: str = "balancesheet",
    ) -> None:
        """
        DQ-04: Validate that total assets and total liabilities
        are balanced within a 1% tolerance.

        A row fails when:

            abs(total_assets - total_liabilities)
            / abs(total_assets) * 100 >= 1%

        Severity:
            WARNING

        Args:
            df: Balance sheet DataFrame.
            table: Table name used in the failure report.
        """

        required_columns = {
            "total_assets",
            "total_liabilities",
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            self.add_failure(
                rule_id="DQ-04",
                severity="CRITICAL",
                table=table,
                message=(
                    "Missing required columns: "
                    + ", ".join(sorted(missing_columns))
                ),
                row_count=len(df),
            )
            return

        data = df.copy()

        data["total_assets"] = pd.to_numeric(
            data["total_assets"],
            errors="coerce",
        )

        data["total_liabilities"] = pd.to_numeric(
            data["total_liabilities"],
            errors="coerce",
        )

        valid_assets = data["total_assets"].abs() > 0

        balance_error = (
            (
                data["total_assets"]
                - data["total_liabilities"]
            ).abs()
            / data["total_assets"].abs()
            * 100
        )

        failures = data[
            valid_assets
            & balance_error.ge(1.0)
        ]

        if not failures.empty:
            self.add_failure(
                rule_id="DQ-04",
                severity="WARNING",
                table=table,
                message=(
                    "Total assets and total liabilities "
                    "differ by 1% or more."
                ),
                row_count=len(failures),
            )
    