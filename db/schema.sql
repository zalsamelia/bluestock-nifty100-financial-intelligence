-- ============================================================
-- Nifty100 Financial Intelligence
-- SQLite Database Schema
-- Sprint 1 - Data Foundation
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. COMPANIES
-- ============================================================

CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT,
    company_logo TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);


-- ============================================================
-- 2. PROFIT AND LOSS
-- ============================================================

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,

    PRIMARY KEY (company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 3. BALANCE SHEET
-- ============================================================

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,

    PRIMARY KEY (company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 4. CASH FLOW
-- ============================================================

CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    PRIMARY KEY (company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 5. ANALYSIS
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis (
    company_id TEXT PRIMARY KEY,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 6. DOCUMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    annual_report TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 7. PROS AND CONS
-- ============================================================

CREATE TABLE IF NOT EXISTS prosandcons (
    company_id TEXT PRIMARY KEY,
    pros TEXT,
    cons TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 8. SECTORS
-- ============================================================

CREATE TABLE IF NOT EXISTS sectors (
    company_id TEXT PRIMARY KEY,
    sector TEXT,
    industry TEXT,
    weight REAL,
    market_cap_category TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 9. STOCK PRICES
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT NOT NULL,
    price_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,

    PRIMARY KEY (company_id, price_date),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- 10. FINANCIAL RATIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    roce_pct REAL,
    return_on_assets_pct REAL,
    debt_to_equity REAL,
    high_leverage_flag INTEGER,
    interest_coverage REAL,
    icr_label TEXT,
    icr_warning_flag INTEGER,
    net_debt_cr REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    cfo_quality_score REAL,
    cfo_quality_label TEXT,
    capex_cr REAL,
    capex_intensity_pct REAL,
    capex_intensity_label TEXT,
    fcf_conversion_pct REAL,
    capital_allocation_pattern TEXT,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    revenue_cagr_3yr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_10yr REAL,
    revenue_cagr_5yr_flag TEXT,
    pat_cagr_3yr REAL,
    pat_cagr_5yr REAL,
    pat_cagr_10yr REAL,
    pat_cagr_5yr_flag TEXT,
    eps_cagr_3yr REAL,
    eps_cagr_5yr REAL,
    eps_cagr_10yr REAL,
    eps_cagr_5yr_flag TEXT,
    composite_quality_score REAL,

    PRIMARY KEY (company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);


-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_profitandloss_company
    ON profitandloss(company_id);

CREATE INDEX IF NOT EXISTS idx_balancesheet_company
    ON balancesheet(company_id);

CREATE INDEX IF NOT EXISTS idx_cashflow_company
    ON cashflow(company_id);

CREATE INDEX IF NOT EXISTS idx_documents_company
    ON documents(company_id);

CREATE INDEX IF NOT EXISTS idx_stock_prices_company
    ON stock_prices(company_id);

CREATE INDEX IF NOT EXISTS idx_financial_ratios_company
    ON financial_ratios(company_id);