# Implementation Plan — Sprint 5: Intelligence, NLP & PDF Reports

**Sprint Horizon**: Days 29–35 | Target Story Points: 70 SP  
**Epics**: Epics 07, 08 & 09 — Cash Flow Intelligence + Reports + NLP  

---

## 1. Executive Summary & Sprint Goal

By the end of Sprint 5, the platform will feature an automated NLP intelligence engine that extracts structured CAGR metrics and dynamically synthesizes high-confidence Pros and Cons for all 92 Nifty 100 constituents across 24 rules (12 Pros + 12 Cons). The Cash Flow Intelligence module will classify all companies by CFO quality, CapEx intensity, capital allocation patterns, distress signals, and deleveraging trends. A publication-grade PDF reporting suite powered by ReportLab will generate all 92 two-page executive tearsheets, 11 sector benchmark reports, and an institutional portfolio summary document.

---

## 2. Proposed Architectural Changes & Modules

```
src/
├── nlp/
│   ├── __init__.py
│   ├── parser.py                # Day 29: Regex parser for analysis.xlsx text fields + CAGR cross-validation
│   └── pros_cons_generator.py   # Day 30: 12 Pro & 12 Con rules engine with confidence scoring
├── analytics/
│   └── cashflow_kpis.py         # Day 31: CFO Quality, CapEx intensity, distress & deleveraging flags
└── reports/
    ├── __init__.py
    ├── tearsheet.py             # Day 33-34: 2-page institutional tearsheet PDF generator (ReportLab)
    ├── sector_report.py         # Day 34: 11 sector comprehensive benchmark PDFs
    └── portfolio_summary.py     # Day 35: Full 92-company portfolio summary PDF with trend indicators
```

---

## 3. Daily Implementation Breakdown

### Day 29 — NLP Analysis Text Parser (`src/nlp/parser.py`)
- Parse raw text strings in `analysis.xlsx` using regex: `(\d+)\s*Years?:?\s*([\d.]+)%`
- Extract targets: `compounded_sales_growth`, `compounded_profit_growth`, `stock_price_cagr`, `roe`
- Outputs:
  - `output/analysis_parsed.csv` (`company_id, metric_type, period_years, value_pct`)
  - `output/parse_failures.csv` (unmatched text entries)
- Cross-validate parsed CAGR against computed values from the Ratio Engine (flag divergence > 5%).

### Day 30 — NLP Auto Pros/Cons Generator (`src/nlp/pros_cons_generator.py`)
- Implement 12 Pro rules and 12 Con rules based on multi-year fundamental trends:
  - **12 Pro Rules**: ROE > 20% (3yr), FCF > 0 (5yr), D/E = 0, Rev CAGR > 15%, OPM > 25%, PAT CAGR > 20%, ICR > 10 / Debt-Free, Div Yield > 2% + FCF>0, EPS CAGR > 15%, ROE improving (3yr), Operating leverage (Rev CAGR > PAT CAGR), Asset growth with declining debt.
  - **12 Con Rules**: D/E > 2.0 (non-financial), FCF < 0 (3yr), OPM declining (3yr), Net loss in latest year, Rev declining (2yr), ICR < 1.5, Div Payout > 100%, D/E rising (3yr), EPS declining (3yr), ROCE < 10%, Net Debt > 3x EBITDA, Rev CAGR < 5%.
- Calculate signal confidence score (0–100%) and filter for `confidence_pct > 60%`.
- Output: `output/pros_cons_generated.csv` (`company_id, type, rule_id, text, confidence_pct`).
- Enforce exit criterion: Every company has $\ge 1$ Pro and $\ge 1$ Con.

### Day 31 & 32 — Cash Flow Intelligence & Capital Allocation (`src/analytics/cashflow_kpis.py`)
- **CFO Quality Score**: $\text{Avg}(\text{CFO} / \text{PAT})$ over 5 years $\rightarrow$ `High Quality` (>1.0), `Moderate` (0.5–1.0), `Accrual Risk` (<0.5).
- **CapEx Intensity**: $|\text{CFI}| / \text{Sales} \times 100$ $\rightarrow$ `Asset Light` (<3%), `Moderate` (3–8%), `Capital Intensive` (>8%).
- **Distress Alert**: $\text{CFO} < 0 \land \text{CFF} > 0$ (raising external financing while burning cash from core operations).
- **Deleveraging Flag**: $\text{CFF} < 0 \land \text{Borrowings declining YoY}$.
- **Capital Allocation YoY Tracking**: Build `output/pattern_changes.csv` mapping changes between the 8 capital allocation archetypes.
- Outputs: `output/cashflow_intelligence.xlsx` (92 rows) and `output/distress_alerts.csv`.

### Day 33 & 34 — Institutional PDF Tearsheet & Sector Reports
- Install `reportlab` dependency and register in `requirements.txt`.
- `src/reports/tearsheet.py`:
  - **Page 1**: Executive Navy banner (`#0A1628`), 6 KPI bento tiles, 10-year Revenue & Net Profit bar chart, ROE vs ROCE trend chart.
  - **Page 2**: Balance Sheet stacked asset/liability bars, Cash Flow waterfall diagram, Pro/Con qualitative bullet points with colored badges, Capital Allocation badge.
  - Full wordwrap, strict height budgeting, and zero layout overflow.
  - Batch generation: `reports/tearsheets/{company_id}_tearsheet.pdf` for all 92 companies.
- `src/reports/sector_report.py`:
  - Batch generation: `reports/sector/{sector_name}_report.pdf` for all 11 sectors.

### Day 35 — Portfolio Summary PDF & Documentation
- `src/reports/portfolio_summary.py`: `reports/portfolio/portfolio_summary.pdf` (alphabetical by ticker, 6 KPIs + $\uparrow/\downarrow/\rightarrow$ trend arrows).
- Update `reports/sprint5_retro.md` and `README.md`.
- Comprehensive test coverage in `tests/nlp/` and `tests/reports/`.

---

## 4. Verification Plan

### Automated Testing
- `tests/nlp/test_parser.py`: Verify regex extraction, field coverage, parse failure logging.
- `tests/nlp/test_pros_cons.py`: Verify 24 rules, confidence thresholds, and $\ge 1$ Pro / $\ge 1$ Con for all 92 companies.
- `tests/analytics/test_cashflow_kpis.py`: Verify CFO quality labels, CapEx intensity, distress flags, Excel schema.
- `tests/reports/test_reports.py`: Verify generation of 92 tearsheets, 11 sector reports, and portfolio summary PDF ($\ge 30\text{ KB}$ per file, non-empty, valid PDF structure).
- Full regression test run: `pytest`.

### Manual & Visual Quality Inspection
- Inspect sample tearsheets across multiple sectors (TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL) to confirm clean layouts, crisp typography, and zero text overlap.
