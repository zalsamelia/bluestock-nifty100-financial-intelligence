"""
Generate a reproducible 5-company Sprint 1 manual-review pack.

The script selects five companies deterministically (seed=2026) and
exports one row per company with P&L/BS/CF coverage plus latest-year
sanity checks. The analyst must inspect the selected companies manually.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query("SELECT * FROM companies", conn)
        company_col = "id" if "id" in companies.columns else "company_id"
        universe = companies[company_col].dropna().astype(str).sort_values().tolist()

        selected = (
            pd.Series(universe)
            .sample(n=min(5, len(universe)), random_state=2026)
            .sort_values()
            .tolist()
        )

        rows = []

        for company_id in selected:
            row = {"company_id": company_id}

            for table in ("profitandloss", "balancesheet", "cashflow"):
                df = pd.read_sql_query(
                    f"SELECT * FROM [{table}] WHERE company_id = ?",
                    conn,
                    params=(company_id,),
                )
                row[f"{table}_years"] = int(df["year"].nunique()) if not df.empty else 0
                row[f"{table}_rows"] = int(len(df))

                if not df.empty:
                    latest = df.sort_values("year").iloc[-1]
                    row[f"{table}_latest_year"] = latest["year"]
                else:
                    row[f"{table}_latest_year"] = None

            bs = pd.read_sql_query(
                """
                SELECT year, total_assets, total_liabilities
                FROM balancesheet
                WHERE company_id = ?
                ORDER BY year DESC
                LIMIT 1
                """,
                conn,
                params=(company_id,),
            )
            if not bs.empty:
                assets = float(bs.iloc[0]["total_assets"])
                liabilities = float(bs.iloc[0]["total_liabilities"])
                row["latest_bs_balance_pct"] = (
                    abs(assets - liabilities) / abs(assets) * 100
                    if assets != 0 else None
                )
            else:
                row["latest_bs_balance_pct"] = None

            pnl = pd.read_sql_query(
                """
                SELECT year, sales, operating_profit, opm_percentage
                FROM profitandloss
                WHERE company_id = ?
                ORDER BY year DESC
                LIMIT 1
                """,
                conn,
                params=(company_id,),
            )
            if not pnl.empty and float(pnl.iloc[0]["sales"]) != 0:
                sales = float(pnl.iloc[0]["sales"])
                op = float(pnl.iloc[0]["operating_profit"])
                row["latest_source_opm"] = pnl.iloc[0]["opm_percentage"]
                row["latest_computed_opm"] = op / sales * 100
            else:
                row["latest_source_opm"] = None
                row["latest_computed_opm"] = None

            rows.append(row)

    output = REPORT_DIR / "manual_review_5_companies.csv"
    review = pd.DataFrame(rows)
    review.to_csv(output, index=False)

    print("=" * 70)
    print("SPRINT 1 MANUAL REVIEW PACK")
    print("=" * 70)
    print(f"Selected companies: {', '.join(selected)}")
    print(f"File: {output}")
    print()
    print(review.to_string(index=False))
    print()
    print("MANUAL ACTION:")
    print("1. Open each selected company's P&L, BS and CF rows.")
    print("2. Confirm latest year is plausible.")
    print("3. Inspect BS balance percentage.")
    print("4. Inspect source OPM vs computed OPM.")
    print("5. Record any issue in the Sprint 1 review notes.")
    print("=" * 70)


if __name__ == "__main__":
    main()
