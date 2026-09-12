# Nifty 100 Financial Intelligence & Analytics Platform

Institutional-grade fundamental equity analytics platform and interactive Streamlit dashboard for the **Nifty 100 universe (2011–2024)**.

---

## Key Capabilities & Features

### 1. **Interactive 8-Screen Streamlit Dashboard**
- **01 Home Overview (`pages/01_home.py`)**: 6 universe summary KPI tiles, Plotly 11-sector composition donut chart, Top-5 Quality Score companies table, and fiscal year selector (2019–2024).
- **02 Company Profile (`pages/02_profile.py`)**: Autocomplete search across 92 companies, 6 key KPI cards, 10-year Revenue & Net Profit historical bar chart, ROE vs ROCE dual-axis line chart, and qualitative Pros/Cons investment badges.
- **03 Financial Screener (`pages/03_screener.py`)**: 10 real-time metric sliders, 6 quick-preset template buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live result count banner, and one-click CSV export.
- **04 Peer Comparison (`pages/04_peers.py`)**: 11 peer group selectors, 8-axis interactive Plotly `Scatterpolar` radar chart (Company polygon vs Peer Group dashed average), and side-by-side KPI comparison table with gold benchmark row highlight.
- **05 Trend Analysis (`pages/05_trends.py`)**: Multi-metric historical overlay (up to 3 metrics) on a 10-year line chart with interactive YoY % change annotations on data points.
- **06 Sector Dynamics (`pages/06_sectors.py`)**: Broad sector selector, Plotly bubble chart (X: Sales, Y: ROE, Size: Market Cap, Color: Industry), and cross-sector median KPI benchmark bar chart.
- **07 Capital Allocation Map (`pages/07_capital.py`)**: Plotly Treemap categorizing all 92 companies into the 8 capital allocation archetypes with drill-down company lists.
- **08 Annual Reports Repository (`pages/08_reports.py`)**: Chronological annual report repository with direct BSE PDF filing links and real-time availability badges.

---

### 2. **Financial Ratio & Valuation Analytics**
- **Ratio Engine (`src/analytics/ratios.py`, `cagr.py`, `cashflow_kpis.py`)**: 38 calculated ratios across 14 fiscal years in SQLite `financial_ratios` table.
- **Valuation Module (`src/analytics/valuation.py`)**: Computes FCF Yield, Sector Median P/E, 5-Year Historical Median P/E, and classifies companies into `Caution` (Overvalued), `Discount` (Undervalued), or `Fair` valuation bands.
- **Excel Outputs**:
  - `output/screener_output.xlsx` — 6 preset sheets with green/red conditional fills.
  - `output/peer_comparison.xlsx` — 11 peer group sheets with gold benchmark highlights and peer medians.
  - `output/valuation_summary.xlsx` — 92 companies with valuation multiples and flags.
  - `output/valuation_flags.csv` — Filtered list of Caution/Discount companies.
  - `reports/radar_charts/` — 92 standalone PNG radar charts.

### 3. **NLP Intelligence & Cash Flow Analytics (Sprint 5)**
- **Analysis Text Parser (`src/nlp/parser.py`)**: Regex-driven parser extracting multi-period CAGR values from qualitative disclosures with automated cross-validation.
- **Auto Pros & Cons Generator (`src/nlp/pros_cons_generator.py`)**: 24-rule heuristic engine (12 Pros, 12 Cons) evaluating capital efficiency, leverage, cash flow quality, and operating momentum with signal confidence thresholding.
- **Cash Flow Intelligence (`src/analytics/cashflow_kpis.py`)**: Computes 5-Year CFO Quality Scores, CapEx Intensity tiers, Distress Alerts ($CFO < 0 \land CFF > 0$), and Deleveraging momentum.

---

### 4. **Publication-Grade PDF Reporting Suite (ReportLab)**
- **Company Tearsheets (`src/reports/tearsheet.py`)**: 92 two-page institutional PDF tearsheets featuring bento KPI tiles, 10-year Revenue & Profit charts, ROE/ROCE return profiles, Balance Sheet composition, Cash Flow waterfall, and qualitative Pros/Cons bullets.
- **Sector Benchmark Reports (`src/reports/sector_report.py`)**: 11 sector PDF landscape documents with median KPI benchmarks and full constituent performance matrices.
- **Portfolio Summary (`src/reports/portfolio_summary.py`)**: Alphabetical 92-company executive catalog with directional trend arrows ($\uparrow / \downarrow / \rightarrow$).

---

## Quick Start Guide

### Prerequisites
- Python 3.10+
- SQLite3
- Required packages installed via pip / conda

### Installation
```bash
# Clone the repository
git clone https://github.com/zalsamelia/bluestock-nifty100-financial-intelligence.git
cd nifty100-financial-intelligence

# Install dependencies
pip install -r requirements.txt
```

### Launching the Dashboard
To start the multi-page Streamlit application on `localhost:8501`:
```bash
streamlit run src/dashboard/app.py
```

### Running Pipelines & Analytics
```bash
# Run Sprint 2 ratio calculation pipeline
python scripts/populate_ratios.py

# Run Sprint 3 screener & peer comparison pipeline
python scripts/run_sprint3_pipeline.py

# Run Sprint 4 valuation module
python src/analytics/valuation.py

# Run Sprint 5 NLP text parser & pros/cons generator
python src/nlp/parser.py
python src/nlp/pros_cons_generator.py

# Run Sprint 5 cash flow intelligence engine
python src/analytics/cashflow_kpis.py

# Generate PDF reports suite
python src/reports/tearsheet.py
python src/reports/sector_report.py
python src/reports/portfolio_summary.py
```

### Running Test Suite
```bash
pytest
```
*Current test suite: **119+ passed, 0 failures** across ETL, KPI, Screener, Peer, Valuation, NLP, and Reporting modules.*
