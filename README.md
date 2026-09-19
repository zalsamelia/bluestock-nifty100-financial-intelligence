# Nifty 100 Financial Intelligence & Analytics Platform

Institutional-grade fundamental equity analytics platform, Machine Learning clustering engine, production-ready FastAPI REST server, and interactive Streamlit dashboard for the **Nifty 100 universe (2011–2024)**.

---

## Key Capabilities & Features

### 1. **Interactive Streamlit Dashboard**
- **01 Home Overview (`pages/01_home.py`)**: Universe summary KPI tiles, Plotly 11-sector composition donut chart, Top-5 Quality Score companies table, and fiscal year selector.
- **02 Company Profile (`pages/02_company.py` / `02_profile.py`)**: Autocomplete search across 92 companies, 6 key KPI cards, 10-year Revenue & Net Profit historical bar chart, ROE vs ROCE dual-axis line chart, and qualitative Pros/Cons investment badges.
- **03 Financial Screener (`pages/03_screener.py` / `04_screener.py`)**: 10 real-time metric sliders, 6 quick-preset template buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround), live result count banner, and one-click CSV export.
- **04 Peer Comparison (`pages/04_peers.py` / `05_peer.py`)**: 11 peer group selectors, 8-axis interactive Plotly `Scatterpolar` radar chart (Company polygon vs Peer Group dashed average), and side-by-side KPI comparison table with gold benchmark row highlight.
- **05 Trend Analysis (`pages/05_trends.py`)**: Multi-metric historical overlay (up to 3 metrics) on a 10-year line chart with interactive YoY % change annotations on data points.
- **06 Sector Dynamics (`pages/06_sectors.py`)**: Broad sector selector, Plotly bubble chart (X: Sales, Y: ROE, Size: Market Cap, Color: Industry), and cross-sector median KPI benchmark bar chart.
- **07 Capital Allocation Map (`pages/07_capital.py`)**: Plotly Treemap categorizing all 92 companies into the 8 capital allocation archetypes with drill-down company lists.
- **08 Reports Hub (`pages/08_reports.py` / `07_reports.py`)**: Direct download hub for 92 two-page tearsheet PDFs, 11 sector PDFs, and portfolio summaries.

---

### 2. **Machine Learning Clustering & Behavioral Archetypes (Sprint 6)**
- **KMeans Clustering (`src/analytics/clustering.py`)**: Unsupervised clustering ($k=5$, `random_state=42`) classifying 92 companies into 5 investment archetypes:
  1. *High-Quality Compounders* (51 companies) — High ROE/ROCE, low debt, consistent margin expansion.
  2. *Turnaround Candidates* (16 companies) — Restructuring balance sheets, recovering CFO momentum.
  3. *Defensive Cash Champions* (10 companies) — High dividend yield (>50% payout), steady utility cash flow.
  4. *Value Cyclicals* (9 companies) — Low valuation multiples, economic cycle linkage.
  5. *Emerging Growth* (6 companies) — High revenue CAGR (>18%), aggressive CapEx reinvestment.
- **Visual Analytics**:
  - `reports/elbow_plot.png` — Inertia elbow curve ($k=2$ to $10$) validating $k=5$ cluster optimality.
  - `reports/correlation_heatmap.png` — Pearson correlation matrix across 10 financial ratios.
  - `output/cluster_labels.csv` — Full universe archetype mapping with Euclidean centroid distances.
  - `output/outlier_report.csv` — Sector-relative Z-score anomaly detection.
  - `output/portfolio_stats.csv` — Decile and quartile distributions (P10 to P90) across 10 core KPIs.

---

### 3. **High-Throughput FastAPI REST Server (Sprint 6)**
- **Server Architecture (`src/api/main.py`)**: ASGI application with CORS (`*`), response timing middleware (`X-Process-Time-Ms`), and structured error handlers.
- **16 Production Endpoints mounted under `/api/v1`**:
  - `GET /api/v1/health` — Live row counts for all 10 SQLite tables, uptime, version.
  - `GET /api/v1/companies` — Paginated company list with sector and market cap filters.
  - `GET /api/v1/companies/{ticker}` — Full master profile and latest fiscal year ratios.
  - `GET /api/v1/companies/{ticker}/pl` — 10-year historical Profit & Loss statements.
  - `GET /api/v1/companies/{ticker}/bs` — 10-year historical Balance Sheets.
  - `GET /api/v1/companies/{ticker}/cashflow` — 10-year historical Cash Flows (CFO, CFI, CFF).
  - `GET /api/v1/companies/{ticker}/ratios` — 10-year computed financial ratios.
  - `GET /api/v1/companies/{ticker}/tearsheet` — Direct binary streaming download of 2-page PDF.
  - `GET /api/v1/companies/{ticker}/peers/compare` — 8-axis peer benchmarking radar data.
  - `GET /api/v1/companies/{ticker}/documents` — Annual report links with URL validity verification.
  - `GET /api/v1/screener` — Multi-metric slider screener engine with HTTP 400 parameter validation.
  - `GET /api/v1/sectors` — All 11 Nifty 100 sectors with constituent counts and median KPIs.
  - `GET /api/v1/sectors/{sector}/companies` — Constituents in a given sector (with 404 validation).
  - `GET /api/v1/peers/{group_name}` — Peer group benchmark basket statistics.
  - `GET /api/v1/market-cap/{ticker}` — Real-time derived market capitalization and multiples.
  - `GET /api/v1/portfolio/stats` — Universe-wide percentile benchmarks (P10, P25, P50, P75, P90).
- **API Documentation**:
  - `docs/openapi.json` — Exported OpenAPI 3.0 specification.
  - `docs/postman_collection.json` — Complete Postman collection for all 16 endpoints.

---

### 4. **Financial Ratio, Valuation & Forensic NLP Analytics**
- **Ratio Engine (`src/analytics/ratios.py`, `cagr.py`, `cashflow_kpis.py`)**: 38 calculated ratios across 14 fiscal years stored in SQLite `financial_ratios`.
- **Valuation Module (`src/analytics/valuation.py`)**: DCF intrinsic value, Graham Fair Value, Peter Lynch PEG benchmark, Reverse DCF implied growth, and PE Multiple Bands.
- **NLP Intelligence (`src/nlp/parser.py`, `src/nlp/pros_cons_generator.py`)**: Rule-based parser extracting CAGR statements and 24-rule heuristic engine generating qualitative Pros and Cons with confidence scoring.
- **Cash Flow Intelligence (`src/analytics/cashflow_kpis.py`)**: CFO Quality Scores, CapEx Intensity tiers, Distress Alerts, and capital allocation matrices.

---

### 5. **Institutional PDF Documentation & Quality Assurance**
- **Analyst Guide (`docs/analyst_guide.pdf`)**: 11-page comprehensive institutional technical manual and formula reference guide generated with ReportLab.
- **Acceptance Checklist (`docs/acceptance_checklist.pdf`)**: Formal verification certificate confirming 100% compliance across all 20 Acceptance Gates (AC-01 through AC-20).
- **Automated Test Harness (`reports/pytest_report.html`)**: **197 unit and integration tests passing with 0 failures**.
- **Final Project Sign-Off (`reports/sprint6_signoff.md`)**: Complete Day 45 milestone sign-off and deliverable audit report.
- **Archival Bundle (`output/final_deliverables/`)**: Consolidated directory containing all 23 project artifacts.

---

## Quick Start Guide

### Prerequisites
- Python 3.10+
- SQLite3
- Fast execution via virtual environment (`venv` / `conda`)

### Installation
```bash
# Clone the repository
git clone https://github.com/zalsamelia/bluestock-nifty100-financial-intelligence.git
cd nifty100-financial-intelligence

# Install all dependencies
pip install -r requirements.txt
```

### Launching the REST API Server
To start the FastAPI server on `http://localhost:8000`:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Interactive ReDoc UI: `http://localhost:8000/redoc`

### Launching the Dashboard
To start the interactive Streamlit dashboard on `http://localhost:8501`:
```bash
streamlit run dashboard/app.py
```

### Running Performance Benchmarks & Acceptance Audit
```bash
# Run concurrent API load test & SQLite indexing
python scripts/load_test_api.py

# Run automated 20 Acceptance Gates audit & generate checklist PDF
python scripts/verify_acceptance_gates.py
```

### Running the Test Suite
```bash
pytest -v --html=reports/pytest_report.html --self-contained-html
```
*Current test suite: **197 passed, 0 failures (100% pass rate)** across ETL, KPI, Screener, Peer, Valuation, NLP, Clustering, API, and Reporting modules.*

---

## Project Structure
```text
nifty100-financial-intelligence/
├── config/                  # Screener & peer group YAML configurations
├── data/                    # Raw Excel financial statement workbooks
├── docs/                    # OpenAPI spec, Postman collection, Analyst Guide PDF, Checklist PDF
├── dashboard/               # Streamlit multi-page application
├── output/                  # Generated CSV, XLSX models, and final deliverables
│   └── final_deliverables/  # Consolidated 23 production deliverables
├── reports/                 # Tearsheets (92), Sector PDFs (11), Portfolio PDF, Pytest HTML report
├── scripts/                 # ETL loaders, load testing, and verification harnesses
├── src/                     # Core business logic (analytics, api, etl, nlp, reports)
└── tests/                   # 197 automated unit and integration tests
```

---

## License & Internship Project Attribution
Developed for the **Bluestock Financial Intelligence Internship Project (Sprints 1–6, Days 1–45)**.  
Lead Data Analyst: **Zalsabilah R. A. Arep**
