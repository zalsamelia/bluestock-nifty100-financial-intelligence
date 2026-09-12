# Sprint 5 Retrospective — Intelligence, NLP & PDF Reports

**Sprint**: Sprint 5 — Days 29–35  
**Target Story Points**: 70 SP  
**Epics**: Epic 07 (Cash Flow Intelligence), Epic 08 (Institutional PDF Reporting), Epic 09 (NLP Intelligence Engine)  
**Sprint Goal**: Implement an automated NLP text parsing and Pros/Cons generation engine for all 92 Nifty 100 constituents with confidence scoring. Build the Cash Flow Intelligence module to classify CFO quality, CapEx intensity, distress signals, and capital allocation patterns. Generate all 92 two-page publication-grade tearsheet PDFs, 11 sector benchmark reports, and an institutional portfolio summary PDF with zero text overflow.

---

## 1. Deliverables Completed

| Deliverable | Status | Details & Metrics |
|---|---|---|
| `src/nlp/parser.py` | Complete | Regex parser for `analysis.xlsx` (`(\d+)\s*Years?:?\s*([\d.]+)%`), extracting structured CAGR numbers with cross-validation against financial ratios |
| `src/nlp/pros_cons_generator.py` | Complete | 12 Pro & 12 Con rules engine with signal strength scoring (>60% confidence filter); guarantees $\ge 1$ Pro and $\ge 1$ Con for all 92 companies |
| `output/analysis_parsed.csv` | Complete | Structured CAGR records extracted from raw qualitative text |
| `output/parse_failures.csv` | Complete | Audit log of unmatched text entries |
| `output/pros_cons_generated.csv` | Complete | Comprehensive dataset of 478 fundamental pros and cons across all 92 companies |
| `src/analytics/cashflow_kpis.py` | Complete | CFO Quality Score, CapEx Intensity, Distress Signal detection ($CFO < 0 \land CFF > 0$), Deleveraging tracking |
| `output/cashflow_intelligence.xlsx` | Complete | 92 companies with CFO quality, CapEx intensity, FCF CAGR, conversion %, and capital allocation labels |
| `output/distress_alerts.csv` | Complete | 13 flagged companies exhibiting core operating cash burn financed by external debt/equity |
| `output/pattern_changes.csv` | Complete | 526 historical capital allocation pattern transitions across FY2011–FY2024 |
| `src/reports/tearsheet.py` | Complete | ReportLab 2-page institutional tearsheet generator with bento tiles, high-res matplotlib vector charts, and wordwrapped qualitative cards |
| `reports/tearsheets/*.pdf` | Complete | 92 standalone company tearsheets ($\ge 30\text{ KB}$ each, zero page overflow) |
| `src/reports/sector_report.py` | Complete | Sector benchmark PDF generator covering all 11 peer group sectors and broad market sectors |
| `reports/sector/*.pdf` | Complete | Publication-grade sector landscape reports with median KPIs and complete constituent comparative tables |
| `src/reports/portfolio_summary.py` | Complete | Full 92-company portfolio document with directional trend indicators ($\uparrow/\downarrow/\rightarrow$) |
| `reports/portfolio/portfolio_summary.pdf` | Complete | Multi-page portfolio catalog with executive cover page and methodology notes |

---

## 2. Key Technical & Methodological Decisions

### A. Strict Layout Budgeting in ReportLab
- **Zero Page Overflow**: Implemented strict point/inch budgeting across both pages of the tearsheet to prevent orphaned rows or accidental 3rd pages.
- **Wordwrapped Table Cells**: Encapsulated all qualitative text, company names, and industry descriptions within `reportlab.platypus.Paragraph` objects inside explicitly dimensioned `Table` containers.

### B. High-Resolution Visual Embedding
- Embedded matplotlib-generated vector/high-DPI chart buffers (200 DPI) directly into ReportLab flowables:
  1. 10-Year Revenue & Net Profit Bar Chart (Side-by-side grouped bars in Midnight Navy and Emerald Mint).
  2. 10-Year ROE vs ROCE Trend Line Chart (Dual return profile trajectory).
  3. Balance Sheet Composition Stacked Bar Chart (Equity vs Borrowings vs Other Liabilities).
  4. Cash Flow Waterfall Dynamics (CFO vs CFI vs CFF vs Net Cash Flow).

### C. NLP Rule Engine & Confidence Thresholding
- Evaluated 24 fundamental signal rules (12 Pros and 12 Cons) spanning profitability, liquidity, solvency, operating leverage, and capital efficiency.
- Applied a strict $> 60\%$ confidence filter to eliminate weak statistical signals while maintaining fallback heuristics to ensure every constituent has actionable analytical coverage.

---

## 3. Test Suite & Verification Results

- **New Unit Tests Added**:
  - `tests/nlp/test_parser.py`: Regex matching, multi-period extraction, and cross-validation logic.
  - `tests/nlp/test_pros_cons.py`: 24 rule evaluations, confidence bounds, and $100\%$ universe coverage.
  - `tests/analytics/test_cashflow_kpis.py`: CFO classification, CapEx intensity, CAGR mathematics, and Excel generation.
  - `tests/reports/test_reports.py`: PDF generation, file integrity, and size bounds ($\ge 30\text{ KB}$).
- **Overall Codebase Status**: All tests passing with zero errors.
