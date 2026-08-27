"""
Environment verification for Nifty 100 Financial Intelligence project.

Checks the Python version and required project dependencies.
"""

import sys


REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "openpyxl",
    "xlrd",
    "dotenv",
    "sqlalchemy",
    "pytest",
    "pydantic",
    "yaml",
    "requests",
    "httpx",
    "bs4",
    "lxml",
    "yfinance",
    "matplotlib",
    "seaborn",
    "plotly",
    "jupyter",
    "ipykernel",
]


def main():
    """Verify Python environment and required dependencies."""

    print("=" * 60)
    print("NIFTY 100 FINANCIAL INTELLIGENCE")
    print("ENVIRONMENT CHECK")
    print("=" * 60)

    print(f"Python version: {sys.version.split()[0]}")
    print()

    failed = []

    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[FAIL] {package}")
            failed.append(package)

    print()
    print("=" * 60)

    if failed:
        print("Environment check FAILED.")
        print("Missing packages:")
        for package in failed:
            print(f"- {package}")
        sys.exit(1)

    print("Environment check PASSED.")
    print("=" * 60)


if __name__ == "__main__":
    main()