"""
Unit tests for Peer Comparison & Percentile Ranking Engine (Sprint 3 — Epic 04).
Tests loading 11 peer groups from peer_groups.xlsx, intra-group PERCENT_RANK
computation for 10 metrics, inverse ranking for D/E, benchmark company flags,
unassigned company fallback ('No peer group assigned'), and SQLite database integration.
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from src.analytics.peer import (
    load_peer_groups_mapping,
    compute_peer_percentiles,
    populate_peer_percentiles_table,
    get_company_peer_rankings,
    RANKING_METRICS,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx"


def test_load_peer_groups_mapping():
    """Verify loading 11 peer groups from peer_groups.xlsx with benchmark flags."""
    df = load_peer_groups_mapping(PEER_GROUPS_PATH)
    assert not df.empty
    assert "peer_group_name" in df.columns
    assert "company_id" in df.columns
    assert "is_benchmark" in df.columns

    # Must contain 11 distinct peer groups and 11 benchmark companies
    assert df["peer_group_name"].nunique() == 11
    assert df[df["is_benchmark"] == True]["company_id"].nunique() == 11
    assert len(df) == 56


def test_compute_peer_percentiles_structure():
    """Verify compute_peer_percentiles returns valid DataFrame and unassigned list."""
    percentile_df, unassigned_msgs = compute_peer_percentiles(DB_PATH, PEER_GROUPS_PATH, target_year=2024)

    assert not percentile_df.empty
    assert "company_id" in percentile_df.columns
    assert "peer_group_name" in percentile_df.columns
    assert "metric" in percentile_df.columns
    assert "percentile_rank" in percentile_df.columns

    # 36 companies should be unassigned
    assert len(unassigned_msgs) == 36
    for msg in unassigned_msgs:
        assert msg["status"] == "No peer group assigned"

    # All percentile ranks should be bounded in [0.0, 1.0]
    valid_ranks = percentile_df["percentile_rank"].dropna()
    assert (valid_ranks >= 0.0).all()
    assert (valid_ranks <= 1.0).all()


def test_it_services_highest_roe_percentile():
    """
    Verify Day 21 acceptance criterion:
    Within IT Services peer group, the company with the highest ROE must receive
    the highest percentile rank (1.0).
    """
    percentile_df, _ = compute_peer_percentiles(DB_PATH, PEER_GROUPS_PATH, target_year=2024)
    it_roe = percentile_df[
        (percentile_df["peer_group_name"] == "IT Services") &
        (percentile_df["metric"] == "return_on_equity_pct")
    ].sort_values("value", ascending=False)

    assert not it_roe.empty
    highest_comp = it_roe.iloc[0]
    assert highest_comp["percentile_rank"] == 1.0
    assert highest_comp["company_id"] == "TCS"


def test_de_inverse_percentile_ranking():
    """
    Verify D/E percentile ranking is inverted so that lower debt-to-equity
    yields a higher percentile rank.
    """
    percentile_df, _ = compute_peer_percentiles(DB_PATH, PEER_GROUPS_PATH, target_year=2024)
    it_de = percentile_df[
        (percentile_df["peer_group_name"] == "IT Services") &
        (percentile_df["metric"] == "debt_to_equity")
    ].sort_values("value", ascending=True)

    assert not it_de.empty
    lowest_de_comp = it_de.iloc[0]
    highest_de_comp = it_de.iloc[-1]

    # The company with lowest D/E should have higher percentile rank than the one with highest D/E
    assert lowest_de_comp["percentile_rank"] > highest_de_comp["percentile_rank"]


def test_unassigned_company_lookup():
    """Verify querying an unassigned company returns 'No peer group assigned' without error."""
    # ABB is one of the 36 unassigned companies
    res = get_company_peer_rankings("ABB", DB_PATH, PEER_GROUPS_PATH)
    assert res["status"] == "No peer group assigned"
    assert res["peer_group_name"] is None
    assert res["rankings"] == {}


def test_assigned_benchmark_company_lookup():
    """Verify querying an assigned benchmark company returns status 'Assigned' and is_benchmark=True."""
    # TCS is benchmark in IT Services
    res = get_company_peer_rankings("TCS", DB_PATH, PEER_GROUPS_PATH)
    assert res["status"] == "Assigned"
    assert res["peer_group_name"] == "IT Services"
    assert res["is_benchmark"] is True
    assert len(res["rankings"]) == len(RANKING_METRICS)


def test_sqlite_peer_percentiles_table_population():
    """Verify SQLite peer_percentiles table is populated and queryable."""
    inserted, unassigned_cnt = populate_peer_percentiles_table(DB_PATH, PEER_GROUPS_PATH, target_year=2024)
    assert inserted == 560  # 56 companies * 10 metrics
    assert unassigned_cnt == 36

    conn = sqlite3.connect(str(DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    conn.close()
    assert count == 560
