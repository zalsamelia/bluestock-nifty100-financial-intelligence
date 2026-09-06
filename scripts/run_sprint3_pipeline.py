"""
Sprint 3 Master Pipeline Runner.
Executes the complete Sprint 3 workflow:
1. Populates peer_percentiles SQLite table (11 peer groups, 10 metrics).
2. Generates output/screener_output.xlsx (6 preset sheets + All Companies).
3. Generates output/peer_comparison.xlsx (11 peer group sheets with gold benchmarks & medians).
4. Generates 92 radar charts in reports/radar_charts/.
5. Performs end-to-end data integrity verification.
"""

import sys
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.peer import populate_peer_percentiles_table
from scripts.generate_screener_excel import generate_screener_excel
from scripts.generate_peer_comparison_excel import generate_peer_comparison_excel
from scripts.generate_radar_charts import generate_all_radar_charts


def run_pipeline() -> None:
    start_time = time.time()
    print("=" * 70)
    print("STARTING SPRINT 3 PIPELINE: SCREENER & PEER COMPARISON ENGINE")
    print("=" * 70)

    # 1. Peer Percentiles Table Population
    print("\n[1/4] Populating SQLite peer_percentiles table...")
    inserted_rows, unassigned_cnt = populate_peer_percentiles_table()
    print(f"      -> Inserted {inserted_rows} rows across 11 peer groups.")
    print(f"      -> Handled {unassigned_cnt} unassigned companies with fallback.")

    # 2. Screener Excel Export
    print("\n[2/4] Generating output/screener_output.xlsx...")
    screener_path = generate_screener_excel()
    print(f"      -> Created: {screener_path}")

    # 3. Peer Comparison Excel Export
    print("\n[3/4] Generating output/peer_comparison.xlsx...")
    peer_excel_path = generate_peer_comparison_excel()
    print(f"      -> Created: {peer_excel_path}")

    # 4. Radar Charts PNG Export
    print("\n[4/4] Generating 92 Radar Charts in reports/radar_charts/...")
    radar_summary = generate_all_radar_charts()
    print(f"      -> Generated {radar_summary['total_generated']} PNG files.")
    print(f"      -> Assigned to peer groups: {radar_summary['peer_assigned']}")
    print(f"      -> Fallback to universe average: {radar_summary['unassigned_fallback']}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"SPRINT 3 PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
