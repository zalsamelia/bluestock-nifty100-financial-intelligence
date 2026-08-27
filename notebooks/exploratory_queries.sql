-- ============================================================
-- Nifty100 Financial Intelligence
-- Sprint 1 - Exploratory SQL Queries
-- ============================================================
-- Run against nifty100.db
-- Based on the confirmed Sprint 1 database schema.
-- ============================================================


-- ============================================================
-- Q01. Row counts for all loader-managed tables
-- ============================================================

SELECT 'companies' AS table_name, COUNT(*) AS row_count
FROM companies

UNION ALL

SELECT 'profitandloss', COUNT(*)
FROM profitandloss

UNION ALL

SELECT 'balancesheet', COUNT(*)
FROM balancesheet

UNION ALL

SELECT 'cashflow', COUNT(*)
FROM cashflow

UNION ALL

SELECT 'analysis', COUNT(*)
FROM analysis

UNION ALL

SELECT 'documents', COUNT(*)
FROM documents

UNION ALL

SELECT 'prosandcons', COUNT(*)
FROM prosandcons

UNION ALL

SELECT 'sectors', COUNT(*)
FROM sectors

UNION ALL

SELECT 'stock_prices', COUNT(*)
FROM stock_prices

UNION ALL

SELECT 'financial_ratios', COUNT(*)
FROM financial_ratios

ORDER BY table_name;


-- ============================================================
-- Q02. Company coverage in P&L, BS and CF
-- ============================================================

SELECT
    c.company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS pnl_years,
    COUNT(DISTINCT b.year) AS bs_years,
    COUNT(DISTINCT f.year) AS cf_years
FROM companies c
LEFT JOIN profitandloss p
    ON p.company_id = c.company_id
LEFT JOIN balancesheet b
    ON b.company_id = c.company_id
LEFT JOIN cashflow f
    ON f.company_id = c.company_id
GROUP BY
    c.company_id,
    c.company_name
ORDER BY
    pnl_years,
    bs_years,
    cf_years,
    c.company_id;


-- ============================================================
-- Q03. Companies with less than 5 years in any core annual table
-- ============================================================

SELECT
    c.company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS pnl_years,
    COUNT(DISTINCT b.year) AS bs_years,
    COUNT(DISTINCT f.year) AS cf_years
FROM companies c
LEFT JOIN profitandloss p
    ON p.company_id = c.company_id
LEFT JOIN balancesheet b
    ON b.company_id = c.company_id
LEFT JOIN cashflow f
    ON f.company_id = c.company_id
GROUP BY
    c.company_id,
    c.company_name
HAVING
    COUNT(DISTINCT p.year) < 5
    OR COUNT(DISTINCT b.year) < 5
    OR COUNT(DISTINCT f.year) < 5
ORDER BY
    c.company_id;


-- ============================================================
-- Q04. Latest-year Balance Sheet imbalance
-- ============================================================

WITH latest AS (
    SELECT
        company_id,
        year,
        total_assets,
        total_liabilities,
        ABS(total_assets - total_liabilities)
            / NULLIF(ABS(total_assets), 0) * 100 AS imbalance_pct,
        ROW_NUMBER() OVER (
            PARTITION BY company_id
            ORDER BY year DESC
        ) AS rn
    FROM balancesheet
)

SELECT
    company_id,
    year,
    total_assets,
    total_liabilities,
    imbalance_pct
FROM latest
WHERE rn = 1
ORDER BY
    imbalance_pct DESC;


-- ============================================================
-- Q05. OPM source vs computed OPM
-- ============================================================

SELECT
    company_id,
    year,
    sales,
    operating_profit,
    opm_percentage AS source_opm,
    operating_profit
        / NULLIF(sales, 0) * 100 AS computed_opm,
    ABS(
        opm_percentage
        - operating_profit / NULLIF(sales, 0) * 100
    ) AS difference_pp
FROM profitandloss
WHERE sales > 0
ORDER BY
    difference_pp DESC;


-- ============================================================
-- Q06. Non-financial companies with non-positive sales
-- ============================================================

SELECT
    p.company_id,
    p.year,
    p.sales,
    s.sector,
    s.industry
FROM profitandloss p
JOIN sectors s
    ON s.company_id = p.company_id
WHERE p.sales <= 0
  AND LOWER(COALESCE(s.sector, '')) NOT LIKE '%financial%'
  AND LOWER(COALESCE(s.sector, '')) NOT LIKE '%bank%'
ORDER BY
    p.company_id,
    p.year;


-- ============================================================
-- Q07. Net cash flow reconciliation
-- ============================================================

SELECT
    company_id,
    year,
    operating_activity,
    investing_activity,
    financing_activity,
    net_cash_flow,
    operating_activity
        + investing_activity
        + financing_activity AS computed_net_cash_flow,
    ABS(
        net_cash_flow
        - (
            operating_activity
            + investing_activity
            + financing_activity
        )
    ) AS difference_cr
FROM cashflow
ORDER BY
    difference_cr DESC;


-- ============================================================
-- Q08. Tax-rate and dividend-payout anomalies
-- ============================================================

SELECT
    company_id,
    year,
    tax_percentage,
    dividend_payout
FROM profitandloss
WHERE tax_percentage < 0
   OR tax_percentage > 60
   OR dividend_payout > 200
ORDER BY
    company_id,
    year;


-- ============================================================
-- Q09. Financial ratio coverage by company
-- ============================================================

SELECT
    company_id,
    COUNT(DISTINCT year) AS ratio_years,
    MIN(year) AS first_year,
    MAX(year) AS last_year
FROM financial_ratios
GROUP BY
    company_id
ORDER BY
    ratio_years,
    company_id;


-- ============================================================
-- Q10. Sector distribution
-- ============================================================

SELECT
    s.sector,
    COUNT(*) AS company_count
FROM sectors s
GROUP BY
    s.sector
ORDER BY
    company_count DESC,
    s.sector;
