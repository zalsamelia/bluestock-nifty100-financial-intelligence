"""
Unit tests for normalize_ticker().
"""

import pytest

from src.etl.normaliser import normalize_ticker


@pytest.mark.parametrize(
    "raw_value, expected",
    [
        ("RELIANCE", "RELIANCE"),
        ("reliance", "RELIANCE"),
        ("Reliance", "RELIANCE"),
        (" TCS ", "TCS"),
        (" tcs ", "TCS"),
        ("HDFCBANK", "HDFCBANK"),
        ("hdfcbank", "HDFCBANK"),
        ("INFY", "INFY"),
        (" infy ", "INFY"),
        ("ICICI BANK", "ICICI BANK"),
        ("icici bank", "ICICI BANK"),
        ("  SBIN  ", "SBIN"),
        ("LT", "LT"),
        ("  TATASTEEL  ", "TATASTEEL"),
        ("MARUTI", "MARUTI"),
        (None, None),
        ("", None),
        ("   ", None),
        ("\t", None),
        ("  RELIANCE   ", "RELIANCE"),
    ],
)
def test_normalize_ticker(raw_value, expected):
    """
    Test ticker normalization across valid and missing inputs.
    """

    assert normalize_ticker(raw_value) == expected