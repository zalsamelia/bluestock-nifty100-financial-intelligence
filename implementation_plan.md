# Implementation Plan — Sprint 6: API Server, Clustering & Final QA

**Sprint Horizon**: Days 36–45 | Target Story Points: 89 SP  
**Epics**: Epics 10, 11 & 12 — Clustering + REST API + QA + Final Sign-Off  

---

## 1. Executive Summary & Sprint Goal

By the end of Sprint 6, the platform will feature an unsupervised machine learning clustering engine that groups all 92 Nifty 100 constituents into 5 distinct financial archetypes using KMeans with standardized multi-dimensional metrics. A high-performance FastAPI REST API server (`src/api/main.py`) will provide 16 institutional endpoints with SQLite connection pooling, CORS, and request logging middleware. The automated test suite will be expanded to achieve comprehensive coverage across ETL, KPI, Screener, Valuation, NLP, API, and Reporting modules with zero failures. Finally, all 20 Acceptance Gates will be systematically audited and verified, culminating in the formal Day 45 Project Acceptance Sign-Off and a 10+ page Analyst Guide PDF.

---

## 2. Architecture & Directory Blueprint

```
src/
├── analytics/
│   ├── clustering.py            # Day 36 & 37: KMeans clustering, elbow plot, Z-score outliers, portfolio stats
│   ├── ratios.py
│   ├── valuation.py
│   └── cashflow_kpis.py
├── api/
│   ├── __init__.py
│   ├── main.py                  # Day 38: FastAPI entrypoint, CORS, logging middleware, prefix /api/v1
│   └── routers/
│       ├── __init__.py
│       ├── health.py            # GET /api/v1/health (10 table counts, uptime, status)
│       ├── companies.py         # GET /api/v1/companies, /{ticker}, /pl, /bs, /cashflow, /ratios, /tearsheet
│       ├── screener.py          # GET /api/v1/screener (multi-slider filters)
│       ├── sectors.py           # GET /api/v1/sectors, /{sector}/companies
│       ├── peers.py             # GET /api/v1/peers/{group_name}, /companies/{ticker}/peers/compare
│       ├── valuation.py         # GET /api/v1/market-cap/{ticker}
│       ├── portfolio.py         # GET /api/v1/portfolio/stats
│       └── documents.py         # GET /api/v1/companies/{ticker}/documents
├── nlp/
└── reports/
docs/
├── openapi.json                 # Day 40: OpenAPI 3.0 specification export
├── postman_collection.json      # Day 40: Postman Collection JSON export
├── analyst_guide.pdf            # Day 44: 10+ Page Institutional User Manual PDF
└── acceptance_checklist.pdf     # Day 45: 23 Deliverables Formal Sign-Off Matrix
```

---

## 3. Daily Implementation Breakdown

### Day 36 & 37 — KMeans Clustering, Profiling & Portfolio Statistics
- **Module**: `src/analytics/clustering.py`
- **Features**: `return_on_equity_pct`, `debt_to_equity`, `revenue_cagr_5yr`, `fcf_cagr_5yr`, `operating_profit_margin_pct`.
- **Pre-processing**: Sector median imputation for missing values $\rightarrow$ `StandardScaler` normalization.
- **KMeans**: $k=5$, `random_state=42`. Generate inertia elbow plot ($k=2 \dots 10$) $\rightarrow$ `reports/elbow_plot.png`.
- **Archetype Profiling**: Compute cluster mean & median profiles to assign 5 descriptive archetypes:
  1. *High-Quality Compounders*
  2. *Defensive Cash Champions*
  3. *Emerging Growth & Capital Expanders*
  4. *Value & Debt-Leveraged Cyclicals*
  5. *Turnaround & Restructuring Candidates*
- **Correlation & Outlier Analysis**:
  - 10-KPI Pearson correlation heatmap $\rightarrow$ `reports/correlation_heatmap.png`.
  - Sector-relative Z-score outlier detection ($|Z| > 3$) $\rightarrow$ `output/outlier_report.csv`.
  - Portfolio percentiles ($P_{10}, P_{25}, P_{50}, P_{75}, P_{90}, \mu, \sigma$) $\rightarrow$ `output/portfolio_stats.csv`.
  - Cluster assignments with distance from centroid $\rightarrow$ `output/cluster_labels.csv`.

### Day 38, 39 & 40 — FastAPI REST API Server (16 Endpoints)
- **Framework**: FastAPI + Uvicorn with SQLite async/threaded access layer.
- **Middleware**: CORS (`allow_origins=["*"]`) and Request Timing Logger.
- **16 Core Endpoints**:
  1. `GET /api/v1/health`: Returns status, uptime, and row counts for all 10 tables.
  2. `GET /api/v1/companies`: Lists 92 companies with search, sector, and cap category filtering.
  3. `GET /api/v1/companies/{ticker}`: Full company profile, metadata, and latest ratios (404 handling).
  4. `GET /api/v1/companies/{ticker}/pl`: 10-year P&L history with `from_year` / `to_year` filters.
  5. `GET /api/v1/companies/{ticker}/bs`: 10-year Balance Sheet history.
  6. `GET /api/v1/companies/{ticker}/cashflow`: 10-year Cash Flow history.
  7. `GET /api/v1/companies/{ticker}/ratios`: Computed financial ratios per fiscal year.
  8. `GET /api/v1/companies/{ticker}/tearsheet`: Direct binary PDF streaming (`application/pdf`).
  9. `GET /api/v1/screener`: Multi-parameter fundamental filter engine (400 validation).
  10. `GET /api/v1/sectors`: 11 sector summaries with median ROE, P/E, D/E, and constituent counts.
  11. `GET /api/v1/sectors/{sector}/companies`: All companies in a sector (404 validation).
  12. `GET /api/v1/peers/{group_name}`: Percentile ranks across 10 metrics for peer group (404 validation).
  13. `GET /api/v1/companies/{ticker}/peers/compare`: 8-axis radar comparison data vs peer benchmark.
  14. `GET /api/v1/market-cap/{ticker}`: Historical valuation multiples (P/E, P/B, EV/EBITDA, Div Yield).
  15. `GET /api/v1/portfolio/stats`: Distribution percentiles table across the universe.
  16. `GET /api/v1/companies/{ticker}/documents`: Annual report filings with URL validity boolean.
- **Specification Exports**: `docs/openapi.json` and `docs/postman_collection.json`.

### Day 41 & 42 — Comprehensive Test Suite & QA Expansion
- **ETL & Normalization**: `tests/etl/test_normalise.py` (20 tests), `tests/etl/test_loader.py` (10 tests).
- **KPI & Ratio Engine**: `tests/kpi/test_ratios.py` (20 tests covering edge cases, negative equity, division by zero).
- **Data Quality Rules**: `tests/dq/test_rules.py` (14 tests verifying each of the 14 DQ rules).
- **FastAPI Endpoints**: `tests/api/test_health.py`, `tests/api/test_companies.py`, `tests/api/test_screener.py`, `tests/api/test_sectors.py`.
- **HTML Report**: Generate `reports/pytest_report.html`.

### Day 43 — Performance Benchmarking & SQLite Optimization
- Concurrent load test: 10 parallel screener requests using `concurrent.futures`. Target: $< 10\text{ s}$.
- Company Profile load time audit ($< 3\text{ s}$).
- Add SQLite indexes (`idx_ratios_cid_yr`, `idx_pl_cid_yr`, etc.) for sub-millisecond query execution.
- Performance audit notes logged to `output/perf_notes.md`.

### Day 44 — 10+ Page Institutional Analyst Guide PDF & Archival
- `docs/analyst_guide.pdf`: Publication-grade 10+ page institutional user manual created with ReportLab:
  1. Platform Architecture & Data Pipeline
  2. 8-Screen Interactive Streamlit Dashboard Guide
  3. Financial Screener & Custom Metric Queries
  4. Valuation & Capital Allocation Methodology
  5. NLP Rule Engine & Confidence Metrics
  6. REST API Reference & cURL Integration Examples
  7. ReportLab PDF Generation & Automation
  8. Troubleshooting, Edge Cases & Data Quality Rules
  9. Acceptance Sign-Off & Verification Matrix
  10. Appendix: Formula Dictionary & SQL Schemas
- Archive all 23 project deliverables into `output/final_deliverables/`.

### Day 45 — 20 Acceptance Gates & Formal Sign-Off
- Execute automated sign-off audit script verifying Gates AC-01 through AC-20.
- Generate `docs/acceptance_checklist.pdf` and `reports/sprint6_signoff.md`.

---

## 4. Verification & Testing Strategy
- Automated unit and integration testing via `pytest`.
- FastAPI server live validation using `TestClient` and live HTTP calls.
- Full regression check across Sprint 1–6 modules.
