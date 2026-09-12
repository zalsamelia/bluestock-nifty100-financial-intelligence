"""
NLP Intelligence Package (Sprint 5).
Includes:
- Analysis Text Parser (parser.py)
- Automated Pros & Cons Generator (pros_cons_generator.py)
"""

from .parser import parse_analysis_file, cross_validate_cagr
from .pros_cons_generator import generate_all_pros_cons

__all__ = [
    "parse_analysis_file",
    "cross_validate_cagr",
    "generate_all_pros_cons"
]
