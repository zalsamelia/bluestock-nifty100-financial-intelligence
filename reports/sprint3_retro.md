# Sprint 3 Retrospective — Screener & Peer Comparison Engine

**Sprint**: Sprint 3 — Days 15–21  
**Target Story Points**: 49 SP  
**Epics**: Epic 03 (Financial Screener Engine) & Epic 04 (Peer Comparison Engine)  
**Sprint Goal**: Implement a flexible financial screener engine supporting 15 metrics, custom thresholds via YAML config, and 6 preset filters. Compute intra-group percentile rankings for 11 peer groups across 10 metrics. Export formatted Excel reports (`screener_output.xlsx`, `peer_comparison.xlsx`) and generate 92 radar chart PNGs. Ensure 100% test pass rate across data quality and analytics modules.

---

## Deliverables Completed

| Deliverable | Status | Details & Metrics |
|---|---|---|
| `config/screener_config.yaml` | ✅ Complete | Analyst-editable thresholds, 6 preset templates, composite score weights, column mappings |
| `src/screener/engine.py` | ✅ Complete | Screener engine core, 15 filter metrics, D/E carve-out, ICR infinity, sector Winsorisation, composite scoring |
| `src/analytics/peer.py` | ✅ Complete | 11 peer groups, 10 metrics `PERCENT_RANK()`, D/E inverted ranking, SQLite database sync |
| `peer_percentiles` SQLite table | ✅ Complete | 560 rows populated across 11 peer groups (10 metrics × 56 assigned companies) |
| `output/screener_output.xlsx` | ✅ Complete | 7 sheets (All Companies + 6 Presets), 27 KPI columns, OpenPyXL green/red threshold cell fills |
| `output/peer_comparison.xlsx` | ✅ Complete | 11 sheets (1 per peer group), 20 KPIs + percentile ranks, gold benchmark highlight, peer median row |
| `reports/radar_charts/` | ✅ Complete | 92 PNG polar radar charts (56 peer-overlay, 36 Nifty 100 universe average fallback) |
| `scripts/run_sprint3_pipeline.py` | ✅ Complete | Automated master pipeline runner executing full Sprint 3 workflow |
| `tests/screener/test_screener_engine.py` | ✅ Complete | 8 unit tests covering config, filters, carve-outs, Winsorisation, scoring, preset yields |
| `tests/peer/test_peer_engine.py` | ✅ Complete | 7 unit tests covering peer groups, rankings, D/E inversion, benchmarks, fallback lookup |
| Full Test Suite (`pytest`) | ✅ Complete | **101 passed, 0 failures, 0 errors** across entire codebase |

---

## Key Technical Decisions & Edge Case Resolutions

### 1. Data Source Mapping for 15 Screener Metrics
To ensure zero ambiguity and high data integrity, all 15 filterable metrics were mapped directly to verified SQLite database columns and raw Excel data:
- **`financial_ratios` table**: `return_on_equity_pct`, `debt_to_equity`, `free_cash_flow_cr`, `revenue_cagr_5yr`, `pat_cagr_5yr`, `operating_profit_margin_pct`, `interest_coverage`, `eps_cagr_5yr`, `asset_turnover`.
- **`market_cap.xlsx`**: `pe_ratio`, `pb_ratio`, `dividend_yield_pct`, `market_cap_crore`.
- **`profitandloss` table**: `sales`, `net_profit`.

### 2. Edge Case Filtering Rules
- **Financials Sector D/E Carve-Out**: Companies in the `Financials` sector (23 banks & NBFCs) automatically bypass the maximum `debt_to_equity` threshold filter, preventing spurious exclusions due to balance sheet structure.
- **Interest Coverage Ratio (ICR) Debt-Free Handling**: Companies flagged as `Debt Free` (or with zero interest expense / null interest coverage) are assigned an effective ICR of $\infty$, ensuring they always satisfy any minimum ICR threshold requirement.
- **Turnaround Watch Multi-Year Logic**: Evaluates year-over-year leverage reduction by comparing $D/E_{\text{latest}} < D/E_{\text{previous}}$ alongside 3-year revenue CAGR and positive latest-year free cash flow.

### 3. Sector-Relative Winsorisation & Composite Quality Score (0–100)
- **Winsorisation**: Capping at 10th percentile (P10) and 90th percentile (P90) computed per `broad_sector`. For small sectors (<5 companies), the engine seamlessly falls back to universe-wide P10/P90.
- **MinMax Normalisation**: Scaled to 0–100 range.
- **Inverse Scoring**: Applied for metrics where lower values represent superior financial strength (e.g. `debt_to_equity`: $\text{Score} = 100 - \text{Scaled}$).
- **Weighted Composition**:
  - Profitability (35%): ROE (15%), ROCE (10%), NPM (10%)
  - Cash Quality (30%): FCF 5-yr CAGR (15%), CFO Quality Score (10%), FCF Positive Flag (5%)
  - Growth (20%): Revenue CAGR 5yr (10%), PAT CAGR 5yr (10%)
  - Leverage (15%): D/E Score (10%), ICR Score (5%)

### 4. Preset Screener Yield Validation
All 6 preset templates were verified on the 92-company universe to ensure they meet the acceptance criteria of returning between 5 and 50 companies:
- **Quality Compounder**: 22 companies (Pass)
- **Value Pick**: 7 companies (Pass)
- **Growth Accelerator**: 19 companies (Pass)
- **Dividend Champion**: 30 companies (Pass)
- **Debt-Free Blue Chip**: 18 companies (Pass)
- **Turnaround Watch**: 33 companies (Pass)

### 5. Peer Group Ranking Engine (`PERCENT_RANK`) & Inverse D/E
- Evaluated across 10 core metrics for 11 peer groups from `data/raw/peer_groups.xlsx`.
- **D/E Inverse Rank**: Computed as $1.0 - \text{PERCENT\_RANK}$, ensuring the company with the lowest debt receives the highest rank.
- **Benchmark Company Flag**: Verified 11 benchmark companies (1 per peer group) with gold highlight styling in Excel exports.
- **Unassigned Companies Fallback**: For the 36 companies not assigned to any peer group in `peer_groups.xlsx`, the system returns `"No peer group assigned"` without raising runtime exceptions and generates radar profile charts referenced against the Nifty 100 universe average.

---

## Output Files Summary

1. **`output/screener_output.xlsx`**:
   - 7 Worksheets: `All Companies`, `Quality Compounder`, `Value Pick`, `Growth Accelerator`, `Dividend Champion`, `Debt-Free Blue Chip`, `Turnaround Watch`.
   - Formatted with freeze panes, dark navy headers, and color fills (green for passing criteria, red for failing).
2. **`output/peer_comparison.xlsx`**:
   - 11 Worksheets corresponding to each peer group (`Automobile`, `Banking & Financial Services`, `Cement & Construction`, `Consumer Goods`, `Energy & Power`, `Healthcare & Pharma`, `IT Services`, `Metals & Mining`, `Oil Gas & Fuels`, `Telecom`, `Infrastructure & Industrials`).
   - Color-coded percentile ranks: Green ($\ge 0.75$), Yellow ($0.25 - 0.75$), Red ($\le 0.25$).
   - Gold row background for designated benchmark companies and bottom peer group median row.
3. **`reports/radar_charts/`**:
   - 92 individual high-resolution PNG charts (`{company_id}_radar.png`).
   - 8 axes: ROE, ROCE, NPM, D/E (inverted), FCF, PAT CAGR 5yr, Revenue CAGR 5yr, Composite Quality Score.
   - Dual-polygon plot: Solid blue company shape + dashed orange reference overlay (peer group average or universe average).

---

## Test Suite Summary

- **Total Test Cases**: 101 tests
- **Passing**: 101 (100%)
- **Failures**: 0
- **Execution Time**: ~24 seconds
- **Test Modules**:
  - `tests/etl/test_loader.py` (6 tests)
  - `tests/etl/test_normaliser_dataframe.py` (2 tests)
  - `tests/etl/test_normaliser_ticker.py` (20 tests)
  - `tests/etl/test_normaliser_year.py` (20 tests)
  - `tests/etl/test_validator.py` (8 tests)
  - `tests/kpi/test_cagr.py` (9 tests)
  - `tests/kpi/test_cashflow.py` (5 tests)
  - `tests/kpi/test_leverage.py` (7 tests)
  - `tests/kpi/test_profitability.py` (9 tests)
  - `tests/peer/test_peer_engine.py` (7 tests)
  - `tests/screener/test_screener_engine.py` (8 tests)
