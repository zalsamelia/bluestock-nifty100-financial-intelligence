"""
Excel data loader for Nifty 100 Financial Intelligence.

This module provides reusable functions for loading Excel source files,
normalizing column names and common values, and loading multiple source
files from the raw data directory.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .normaliser import normalize_ticker, normalize_year


SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".xlsm"}

# The Bluestock source Excel files contain a metadata/title row
# before the actual column headers.
SOURCE_HEADER_ROW = 1


def load_excel(
    file_path: str | Path,
    header: int = SOURCE_HEADER_ROW,
) -> pd.DataFrame:
    """
    Load an Excel source file into a pandas DataFrame.

    Args:
        file_path: Path to the Excel file.
        header: Row number containing the actual column headers.
                Defaults to 1 because the source files contain
                a metadata row at row 0.

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        ValueError:
            If the file extension is unsupported.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {path.suffix}. "
            f"Expected one of {SUPPORTED_EXTENSIONS}."
        )

    return pd.read_excel(path, header=header)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names.

    The transformation:
        - strips leading/trailing whitespace
        - converts names to lowercase
        - replaces spaces with underscores
        - removes repeated underscores

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with normalized column names.
    """

    result = df.copy()

    result.columns = (
        result.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
    )

    return result


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply common value normalization to a DataFrame.

    The function:
        - normalizes column names
        - normalizes year columns
        - normalizes ticker/company identifier columns

    Args:
        df: Input DataFrame.

    Returns:
        Normalized DataFrame.
    """

    result = normalize_columns(df)

    for column in result.columns:
        if column in {
            "year",
            "fiscal_year",
            "financial_year",
        }:
            result[column] = result[column].apply(normalize_year)

        if column in {
            "ticker",
            "symbol",
            "stock_ticker",
            "company_id",
        }:
            result[column] = result[column].apply(normalize_ticker)

    return result


def load_and_normalize(
    file_path: str | Path,
) -> pd.DataFrame:
    """
    Load an Excel file and apply standard normalization.

    Args:
        file_path: Path to the Excel source file.

    Returns:
        Normalized DataFrame.
    """

    df = load_excel(file_path)

    return normalize_dataframe(df)


def load_directory(
    directory: str | Path,
) -> dict[str, pd.DataFrame]:
    """
    Load and normalize all supported Excel files in a directory.

    Args:
        directory: Directory containing source Excel files.

    Returns:
        Dictionary mapping filenames to normalized DataFrames.

    Raises:
        FileNotFoundError:
            If the directory does not exist.
    """

    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(
            f"Data directory not found: {directory_path}"
        )

    files = sorted(
        file
        for file in directory_path.iterdir()
        if file.is_file()
        and file.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    datasets: dict[str, pd.DataFrame] = {}

    for file in files:
        datasets[file.name] = load_and_normalize(file)

    return datasets


def get_project_root() -> Path:
    """
    Return the project root directory.

    Returns:
        Absolute path to the project root.
    """

    return Path(__file__).resolve().parents[2]


def get_raw_data_path() -> Path:
    """
    Return the raw source data directory.

    Returns:
        Absolute path to data/raw.
    """

    return get_project_root() / "data" / "raw"


if __name__ == "__main__":
    datasets = load_directory(get_raw_data_path())

    print("=" * 70)
    print("NIFTY 100 EXCEL LOADER")
    print("=" * 70)

    for filename, dataframe in datasets.items():
        print(
            f"{filename}: "
            f"{len(dataframe)} rows × "
            f"{len(dataframe.columns)} columns"
        )