"""
Unit tests for normalize_year().
"""

import pytest

from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    "value, expected",
    [
        (2023, 2023),
        (2024, 2024),
        ("2023", 2023),
        ("2024", 2024),
        (2023.0, 2023),
        ("2023.0", 2023),
        ("FY2023", 2023),
        ("FY 2023", 2023),
        ("FY-2023", 2023),
        ("FY2023-24", 2023),
        ("2023-24", 2023),
        ("Financial Year 2023", 2023),
        ("FY 2024", 2024),
        ("2024-25", 2024),
        (" 2023 ", 2023),
        ("  FY2023  ", 2023),
        (None, None),
        ("", None),
        ("unknown", None),
        ("N/A", None),
    ],
)
def test_normalize_year(value, expected):
    """Test year normalization across valid and invalid inputs."""

    assert normalize_year(value) == expected