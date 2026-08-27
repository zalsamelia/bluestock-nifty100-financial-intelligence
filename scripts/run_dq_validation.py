"""
Run DQ-01 through DQ-16 validation for the Nifty 100 project.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.dq_validator import run_validation


if __name__ == "__main__":
    failures, summary = run_validation()
    critical = int((failures["severity"] == "CRITICAL").sum()) if not failures.empty else 0
    sys.exit(1 if critical else 0)

