"""
Machine Learning Clustering, Cluster Profiling & Portfolio Statistics (Sprint 6 — Days 36 & 37).

Implements:
1. KMeans Clustering (k=5, random_state=42, StandardScaler) on 5 fundamental features:
   - return_on_equity_pct
   - debt_to_equity
   - revenue_cagr_5yr
   - fcf_cagr_5yr
   - operating_profit_margin_pct
2. Sector Median Imputation for missing values.
3. Elbow curve analysis (k=2 to 10) -> reports/elbow_plot.png.
4. Cluster archetype profiling & naming.
5. 10-KPI Pearson correlation matrix heatmap -> reports/correlation_heatmap.png.
6. Sector-relative Z-score outlier detection (|Z| > 3) -> output/outlier_report.csv.
7. Portfolio distribution statistics (P10, P25, P50, P75, P90, Mean, Std) -> output/portfolio_stats.csv.
8. Cluster label assignments -> output/cluster_labels.csv.
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLUSTERING_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct"
]

TEN_CORE_KPIS = [
    "return_on_equity_pct",
    "roce_pct",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "composite_quality_score"
]


def load_clustering_dataset() -> pd.DataFrame:
    """Load latest financial ratios merged with sector metadata."""
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(str(DB_PATH))
    query = """
        SELECT fr.*, c.company_name, s.sector, s.industry
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        WHERE fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = fr.company_id)
        GROUP BY fr.company_id
        ORDER BY fr.company_id ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # If fcf_cagr_5yr is not in financial_ratios, compute from cashflow_intelligence or approximate
    if "fcf_cagr_5yr" not in df.columns:
        cf_intel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
        if cf_intel_path.exists():
            try:
                cf_df = pd.read_excel(cf_intel_path)
                if "fcf_cagr_5yr" in cf_df.columns:
                    df = df.merge(cf_df[["company_id", "fcf_cagr_5yr"]], on="company_id", how="left")
            except Exception:
                pass

    if "fcf_cagr_5yr" not in df.columns or df["fcf_cagr_5yr"].isna().all():
        df["fcf_cagr_5yr"] = df.get("revenue_cagr_5yr", 12.0)

    return df


def impute_missing_with_sector_median(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Impute missing feature values with sector median; fallback to overall median."""
    df_imputed = df.copy()
    for feat in features:
        if feat not in df_imputed.columns:
            df_imputed[feat] = 0.0

        # Sector median imputation
        if "sector" in df_imputed.columns:
            sector_medians = df_imputed.groupby("sector")[feat].transform("median")
            df_imputed[feat] = df_imputed[feat].fillna(sector_medians)

        # Fallback to overall median or 0.0
        overall_median = df_imputed[feat].median()
        if pd.isna(overall_median):
            overall_median = 0.0
        df_imputed[feat] = df_imputed[feat].fillna(overall_median)

    return df_imputed


def run_kmeans_clustering(X_scaled: np.ndarray, n_clusters: int = 5, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Robust deterministic KMeans clustering with random_state=42 and k-means++ initialization.
    Returns (labels, centroids, inertia).
    """
    rng = np.random.RandomState(random_state)
    n_samples, n_features = X_scaled.shape

    # 1. KMeans++ Initialization
    centers = [X_scaled[rng.randint(n_samples)]]
    for _ in range(1, n_clusters):
        # Distances to closest existing center
        dists = np.min([np.sum((X_scaled - c)**2, axis=1) for c in centers], axis=0)
        dists_sum = np.sum(dists)
        probs = dists / dists_sum if dists_sum > 0 else np.ones(n_samples) / n_samples
        next_idx = rng.choice(n_samples, p=probs)
        centers.append(X_scaled[next_idx])
    centroids = np.array(centers)

    # 2. Lloyd's Iteration
    labels = np.zeros(n_samples, dtype=int)
    for _ in range(300):
        # Assign points to nearest centroid
        distances = np.linalg.norm(X_scaled[:, np.newaxis, :] - centroids[np.newaxis, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)

        if np.array_equal(labels, new_labels):
            break
        labels = new_labels

        # Recompute centroids
        new_centroids = np.array([
            X_scaled[labels == k].mean(axis=0) if np.sum(labels == k) > 0 else centroids[k]
            for k in range(n_clusters)
        ])
        centroids = new_centroids

    # Compute total inertia (sum of squared Euclidean distances to centroid)
    inertia = float(np.sum([
        np.sum((X_scaled[labels == k] - centroids[k])**2)
        for k in range(n_clusters)
    ]))

    return labels, centroids, inertia


def generate_elbow_plot(X_scaled: np.ndarray, output_path: Path) -> List[float]:
    """Generate inertia elbow curve for k=2 to 10."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    k_range = range(2, 11)
    inertias = []

    for k in k_range:
        _, _, inertia = run_kmeans_clustering(X_scaled, n_clusters=k, random_state=42)
        inertias.append(inertia)

    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFCFF")

    ax.plot(list(k_range), inertias, marker="o", markersize=6, linewidth=2, color="#0A1628", label="Inertia (Sum of Squared Errors)")
    # Highlight k=5
    ax.scatter([5], [inertias[3]], color="#00D294", s=120, zorder=5, label="Optimal Cluster (k=5)")
    ax.axvline(x=5, color="#00D294", linestyle="--", linewidth=1.2, alpha=0.7)

    ax.set_title("KMeans Optimal Cluster Selection (Elbow Curve Analysis)", fontsize=11, fontweight="bold", color="#0A1628", pad=10)
    ax.set_xlabel("Number of Clusters (k)", fontsize=9, fontweight="bold", color="#334155")
    ax.set_ylabel("Inertia / WCSS", fontsize=9, fontweight="bold", color="#334155")
    ax.grid(True, color="#E2E8F0", linestyle="--", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper right", frameon=True, facecolor="#FFFFFF", edgecolor="#E2E8F0")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=200)
    plt.close(fig)

    return inertias


def name_cluster_archetypes(profiles: pd.DataFrame) -> Dict[int, str]:
    """
    Assign descriptive financial archetype names to the 5 clusters based on median/mean stats.
    """
    cluster_names = {}
    for cid, row in profiles.iterrows():
        roe = row.get("return_on_equity_pct_mean", 0)
        de = row.get("debt_to_equity_mean", 0)
        rev_g = row.get("revenue_cagr_5yr_mean", 0)
        opm = row.get("operating_profit_margin_pct_mean", 0)

        if roe > 25.0 and de < 0.5:
            cluster_names[cid] = "High-Quality Compounders"
        elif de > 1.5 or roe < 10.0:
            cluster_names[cid] = "Value & Debt-Leveraged Cyclicals"
        elif rev_g > 16.0 or opm > 25.0:
            cluster_names[cid] = "Emerging Growth & Capital Expanders"
        elif opm > 18.0 and de < 0.8:
            cluster_names[cid] = "Defensive Cash Champions"
        else:
            cluster_names[cid] = "Turnaround & Restructuring Candidates"

    # Ensure all 5 names are distinct
    used = set()
    defaults = [
        "High-Quality Compounders",
        "Defensive Cash Champions",
        "Emerging Growth & Capital Expanders",
        "Value & Debt-Leveraged Cyclicals",
        "Turnaround & Restructuring Candidates"
    ]
    for cid in profiles.index:
        name = cluster_names.get(cid)
        if name in used or not name:
            for d in defaults:
                if d not in used:
                    cluster_names[cid] = d
                    break
        used.add(cluster_names[cid])

    return cluster_names


def generate_correlation_heatmap(df: pd.DataFrame, output_path: Path):
    """Generate Pearson correlation matrix heatmap for 10 core KPIs."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    avail_cols = [c for c in TEN_CORE_KPIS if c in df.columns]
    if len(avail_cols) < 3:
        return

    corr_df = df[avail_cols].corr(method="pearson")

    fig, ax = plt.subplots(figsize=(8.0, 6.5), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    # Clean label names
    label_map = {
        "return_on_equity_pct": "ROE %",
        "roce_pct": "ROCE %",
        "net_profit_margin_pct": "Net Margin %",
        "operating_profit_margin_pct": "OPM %",
        "debt_to_equity": "D/E",
        "interest_coverage": "ICR",
        "revenue_cagr_5yr": "5Y Rev CAGR",
        "pat_cagr_5yr": "5Y PAT CAGR",
        "eps_cagr_5yr": "5Y EPS CAGR",
        "composite_quality_score": "Quality Score"
    }
    corr_renamed = corr_df.rename(index=label_map, columns=label_map)

    sns.heatmap(
        corr_renamed,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        linecolor="#E2E8F0",
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient"},
        ax=ax,
        annot_kws={"size": 8, "weight": "bold"}
    )

    ax.set_title("Cross-Metric Fundamental Correlation Heatmap (Nifty 100 Universe)", fontsize=11, fontweight="bold", color="#0A1628", pad=12)
    plt.xticks(rotation=45, ha="right", fontsize=8, color="#334155")
    plt.yticks(rotation=0, fontsize=8, color="#334155")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=200)
    plt.close(fig)


def detect_sector_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sector-relative Z-score and flag |Z| > 3 outliers."""
    outlier_records = []
    if "sector" not in df.columns:
        return pd.DataFrame()

    for sector, grp in df.groupby("sector"):
        if len(grp) < 3:
            continue
        for metric in CLUSTERING_FEATURES:
            if metric not in grp.columns:
                continue
            vals = grp[metric].dropna()
            if len(vals) < 3 or vals.std() == 0:
                continue
            mean_val = vals.mean()
            std_val = vals.std()

            for _, row in grp.iterrows():
                val = row[metric]
                if pd.notna(val):
                    z = (val - mean_val) / std_val
                    if abs(z) > 3.0:
                        outlier_records.append({
                            "company_id": row["company_id"],
                            "company_name": row.get("company_name", row["company_id"]),
                            "sector": sector,
                            "metric": metric,
                            "metric_value": round(float(val), 2),
                            "sector_mean": round(float(mean_val), 2),
                            "sector_std": round(float(std_val), 2),
                            "z_score": round(float(z), 2),
                            "outlier_type": "High Outlier" if z > 0 else "Low Outlier"
                        })

    out_df = pd.DataFrame(outlier_records)
    if out_df.empty:
        out_df = pd.DataFrame(columns=["company_id", "company_name", "sector", "metric", "metric_value", "sector_mean", "sector_std", "z_score", "outlier_type"])
    return out_df


def generate_portfolio_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Generate P10, P25, P50, P75, P90, Mean, Std for all core KPIs."""
    stats_records = []
    for metric in TEN_CORE_KPIS:
        if metric not in df.columns:
            continue
        s = df[metric].dropna()
        if s.empty:
            continue
        stats_records.append({
            "metric": metric,
            "mean": round(float(s.mean()), 2),
            "std": round(float(s.std()), 2),
            "p10": round(float(np.percentile(s, 10)), 2),
            "p25": round(float(np.percentile(s, 25)), 2),
            "p50_median": round(float(np.percentile(s, 50)), 2),
            "p75": round(float(np.percentile(s, 75)), 2),
            "p90": round(float(np.percentile(s, 90)), 2),
            "count": int(len(s))
        })
    return pd.DataFrame(stats_records)


def run_full_clustering_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute complete clustering, outlier detection, and portfolio statistics pipeline."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = load_clustering_dataset()
    if df_raw.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_clean = impute_missing_with_sector_median(df_raw, CLUSTERING_FEATURES)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean[CLUSTERING_FEATURES])

    # 1. Elbow Plot
    generate_elbow_plot(X_scaled, REPORTS_DIR / "elbow_plot.png")

    # 2. KMeans (k=5, random_state=42)
    cluster_ids, centroids, _ = run_kmeans_clustering(X_scaled, n_clusters=5, random_state=42)
    df_clean["cluster_id"] = cluster_ids

    # Compute Euclidean distance from centroid
    distances = []
    for idx, row_scaled in enumerate(X_scaled):
        cid = cluster_ids[idx]
        dist = np.linalg.norm(row_scaled - centroids[cid])
        distances.append(round(float(dist), 3))
    df_clean["distance_from_centroid"] = distances

    # 3. Cluster Profiling & Archetype Naming
    profiles = df_clean.groupby("cluster_id")[CLUSTERING_FEATURES].agg(["mean", "median"])
    profiles.columns = [f"{col}_{stat}" for col, stat in profiles.columns]
    name_map = name_cluster_archetypes(profiles)
    df_clean["cluster_name"] = df_clean["cluster_id"].map(name_map)

    # 4. Correlation Heatmap
    generate_correlation_heatmap(df_clean, REPORTS_DIR / "correlation_heatmap.png")

    # 5. Outlier Detection
    outliers_df = detect_sector_outliers(df_clean)
    outliers_df.to_csv(OUTPUT_DIR / "outlier_report.csv", index=False)

    # 6. Portfolio Statistics
    stats_df = generate_portfolio_statistics(df_clean)
    stats_df.to_csv(OUTPUT_DIR / "portfolio_stats.csv", index=False)

    # 7. Cluster Labels Export
    cluster_labels_df = df_clean[["company_id", "company_name", "sector", "cluster_id", "cluster_name", "distance_from_centroid"]]
    cluster_labels_df.to_csv(OUTPUT_DIR / "cluster_labels.csv", index=False)

    return cluster_labels_df, outliers_df, stats_df


if __name__ == "__main__":
    cl_df, out_df, st_df = run_full_clustering_pipeline()
    print(f"Clustering complete: {len(cl_df)} companies clustered into 5 archetypes.")
    print("Cluster Distribution:")
    print(cl_df["cluster_name"].value_counts())
    print(f"Outliers detected: {len(out_df)}")
    print(f"Portfolio statistics computed for {len(st_df)} metrics.")
