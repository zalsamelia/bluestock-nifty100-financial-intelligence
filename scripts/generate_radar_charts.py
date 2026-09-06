"""
Radar Chart Generator — Sprint 3, Day 19.
Produces 8-axis polar radar charts for all 92 Nifty 100 companies.
- Companies with a peer group: company polygon + peer group dashed average overlay.
- Companies without a peer group (36 companies): company polygon + Nifty 100 universe
  average dashed overlay as reference.
Output: reports/radar_charts/{company_id}_radar.png
"""

import sys
import sqlite3
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict, Any, List

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "nifty100.db"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx"
RADAR_OUTPUT_DIR = PROJECT_ROOT / "reports" / "radar_charts"

# 8 axes for radar chart
RADAR_AXES = [
    "return_on_equity_pct",
    "roce_pct",
    "net_profit_margin_pct",
    "debt_to_equity",      # Inverted on chart: higher score = lower debt
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]

AXIS_LABELS = [
    "ROE %",
    "ROCE %",
    "Net Profit\nMargin %",
    "D/E\n(Inverted)",
    "FCF\n(₹ Cr)",
    "PAT\nCAGR 5yr",
    "Revenue\nCAGR 5yr",
    "Composite\nScore",
]


def _load_dataset() -> tuple:
    """Load financial_ratios and peer group mapping, return (ratios_df, peer_map_df, all_companies)."""
    conn = sqlite3.connect(str(DB_PATH))
    ratios_df = pd.read_sql_query("""
        SELECT fr.*, c.company_name
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        WHERE fr.year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    conn.close()

    peer_map_df = pd.read_excel(PEER_GROUPS_PATH)
    return ratios_df, peer_map_df


def _winsorise_for_radar(series: pd.Series) -> pd.Series:
    """Winsorise at P5/P95 and min-max scale to 0-1 range for polygon shape."""
    valid = series.dropna()
    if valid.empty or valid.std() == 0:
        return pd.Series(0.5, index=series.index)
    p5 = np.percentile(valid, 5)
    p95 = np.percentile(valid, 95)
    if p5 == p95:
        return pd.Series(0.5, index=series.index)
    capped = series.clip(lower=p5, upper=p95)
    scaled = (capped - p5) / (p95 - p5)
    return scaled.fillna(0.0)


def _compute_scaled_df(ratios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 0-1 scaled values for all 8 radar axes across all companies.
    D/E is inverted (1 - scaled) so lower debt = higher polygon height.
    """
    scaled = ratios_df[["company_id", "company_name"]].copy()

    for ax in RADAR_AXES:
        if ax not in ratios_df.columns:
            scaled[ax] = 0.0
            continue
        s = _winsorise_for_radar(ratios_df[ax])
        if ax == "debt_to_equity":
            s = 1.0 - s  # Invert: lower D/E = higher radar score
        scaled[ax] = s.values

    return scaled


def _draw_radar_chart(
    company_id: str,
    company_name: str,
    company_vals: List[float],
    reference_vals: List[float],
    reference_label: str,
    output_path: Path,
) -> None:
    """
    Draw and save an 8-axis polar radar chart with:
    - Filled blue polygon for the company
    - Dashed orange overlay for peer group average (or Nifty 100 universe average)
    """
    n = len(RADAR_AXES)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    # Close the polygon by repeating the first point
    angles_closed = angles + [angles[0]]
    comp_vals_closed = company_vals + [company_vals[0]]
    ref_vals_closed = reference_vals + [reference_vals[0]]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#F5F5F5")

    # Draw company polygon
    ax.plot(angles_closed, comp_vals_closed, color="#1A4A8C", linewidth=2.2, linestyle="-")
    ax.fill(angles_closed, comp_vals_closed, color="#1A4A8C", alpha=0.25)

    # Draw reference overlay (peer group avg or universe avg)
    ax.plot(angles_closed, ref_vals_closed, color="#E87722", linewidth=1.8, linestyle="--", label=reference_label)
    ax.fill(angles_closed, ref_vals_closed, color="#E87722", alpha=0.08)

    # Gridlines and axis tick customisation
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=7, color="grey")
    ax.set_xticks(angles)
    ax.set_xticklabels(AXIS_LABELS, fontsize=8.5, color="#333333")
    ax.grid(color="#CCCCCC", linewidth=0.6, linestyle="--")
    ax.spines["polar"].set_visible(False)

    # Legend and title
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8, frameon=True)
    ax.plot([], [], color="#1A4A8C", linewidth=2, label=company_id)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=8.5, frameon=True)

    company_label = company_name if len(company_name) <= 28 else company_name[:26] + ".."
    plt.title(f"{company_label}\n({company_id}) — Radar Profile", fontsize=11, fontweight="bold",
              color="#1F3864", pad=18)
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=130, bbox_inches="tight", facecolor="#FAFAFA")
    plt.close(fig)


def generate_all_radar_charts(
    output_dir: Path = RADAR_OUTPUT_DIR,
    db_path: Path = DB_PATH,
    peer_groups_path: Path = PEER_GROUPS_PATH,
) -> Dict[str, Any]:
    """
    Generate radar chart PNGs for all 92 Nifty 100 companies.
    Returns summary dict with counts.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ratios_df, peer_map_df = _load_dataset()
    scaled_df = _compute_scaled_df(ratios_df)

    # Build peer group -> company mapping
    peer_to_comps: Dict[str, List[str]] = {}
    comp_to_peer: Dict[str, str] = {}
    for _, row in peer_map_df.iterrows():
        cid = row["company_id"]
        pg = row["peer_group_name"]
        peer_to_comps.setdefault(pg, []).append(cid)
        comp_to_peer[cid] = pg

    # Compute peer group averages for each axis (in scaled space)
    peer_avg_vals: Dict[str, List[float]] = {}
    for pg_name, comps in peer_to_comps.items():
        pg_scaled = scaled_df[scaled_df["company_id"].isin(comps)]
        avg_vals = [float(pg_scaled[ax].mean()) if ax in pg_scaled.columns else 0.5 for ax in RADAR_AXES]
        peer_avg_vals[pg_name] = avg_vals

    # Universe average for fallback
    universe_avg = [float(scaled_df[ax].mean()) if ax in scaled_df.columns else 0.5 for ax in RADAR_AXES]

    generated = 0
    assigned_count = 0
    unassigned_count = 0

    for _, row in scaled_df.iterrows():
        cid = row["company_id"]
        cname = str(row.get("company_name", cid))
        comp_vals = [float(row.get(ax, 0.0)) for ax in RADAR_AXES]

        if cid in comp_to_peer:
            peer_name = comp_to_peer[cid]
            ref_vals = peer_avg_vals.get(peer_name, universe_avg)
            ref_label = f"{peer_name} Avg"
            assigned_count += 1
        else:
            ref_vals = universe_avg
            ref_label = "Nifty 100 Avg"
            unassigned_count += 1

        out_path = output_dir / f"{cid}_radar.png"
        _draw_radar_chart(cid, cname, comp_vals, ref_vals, ref_label, out_path)
        generated += 1

    return {
        "total_generated": generated,
        "peer_assigned": assigned_count,
        "unassigned_fallback": unassigned_count,
        "output_dir": str(output_dir),
    }
