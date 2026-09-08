"""
Shared Cached Data Access Layer for Streamlit Dashboard (Sprint 4 — Day 22).
Implements @st.cache_data(ttl=600) on all query functions for optimal response times (<3s).
"""

import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "raw" / "market_cap.xlsx"
PEER_GROUPS_PATH = PROJECT_ROOT / "data" / "raw" / "peer_groups.xlsx"


def _get_connection() -> sqlite3.Connection:
    """Return SQLite database connection."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    return conn


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Return all 92 companies with metadata, joined with sectors."""
    conn = _get_connection()
    query = """
        SELECT c.*, s.sector, s.industry, s.weight, s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        ORDER BY c.company_name ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker: Optional[str] = None, year: Optional[int] = None) -> pd.DataFrame:
    """Return financial ratios for a specific company or all companies, optionally filtered by year."""
    conn = _get_connection()
    conditions = []
    params = []

    if ticker:
        conditions.append("fr.company_id = ?")
        params.append(ticker)
    if year:
        conditions.append("fr.year = ?")
        params.append(year)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"""
        SELECT fr.*, c.company_name, s.sector, s.industry, s.market_cap_category
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        {where_clause}
        ORDER BY fr.year ASC, fr.company_id ASC
    """
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return 10-year Profit & Loss historical data for a company or all companies."""
    conn = _get_connection()
    if ticker:
        query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    else:
        query = "SELECT * FROM profitandloss ORDER BY company_id ASC, year ASC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return 10-year Balance Sheet historical data for a company or all companies."""
    conn = _get_connection()
    if ticker:
        query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    else:
        query = "SELECT * FROM balancesheet ORDER BY company_id ASC, year ASC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return 10-year Cash Flow historical data for a company or all companies."""
    conn = _get_connection()
    if ticker:
        query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    else:
        query = "SELECT * FROM cashflow ORDER BY company_id ASC, year ASC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Return sector and industry mapping for all 92 companies."""
    conn = _get_connection()
    df = pd.read_sql_query("SELECT * FROM sectors ORDER BY sector ASC, company_id ASC", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name: Optional[str] = None) -> pd.DataFrame:
    """Return peer group mappings joined with peer percentiles."""
    conn = _get_connection()
    if group_name:
        query = """
            SELECT pp.*, c.company_name
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.company_id
            WHERE pp.peer_group_name = ?
            ORDER BY pp.metric ASC, pp.percentile_rank DESC
        """
        df = pd.read_sql_query(query, conn, params=(group_name,))
    else:
        query = """
            SELECT pp.*, c.company_name
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.company_id
            ORDER BY pp.peer_group_name ASC, pp.metric ASC, pp.percentile_rank DESC
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_groups_list() -> List[str]:
    """Return list of distinct peer group names."""
    if PEER_GROUPS_PATH.exists():
        pg_df = pd.read_excel(PEER_GROUPS_PATH)
        return sorted(pg_df["peer_group_name"].unique().tolist())
    conn = _get_connection()
    df = pd.read_sql_query("SELECT DISTINCT peer_group_name FROM peer_percentiles ORDER BY peer_group_name ASC", conn)
    conn.close()
    return df["peer_group_name"].tolist()


@st.cache_data(ttl=600)
def get_valuation(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return valuation metrics from market_cap.xlsx merged with company metadata."""
    if MARKET_CAP_PATH.exists():
        mc_df = pd.read_excel(MARKET_CAP_PATH)
    else:
        mc_df = pd.DataFrame()

    if ticker and not mc_df.empty:
        mc_df = mc_df[mc_df["company_id"] == ticker]

    conn = _get_connection()
    comp_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT company_id, sector, industry FROM sectors", conn)
    conn.close()

    if not mc_df.empty:
        merged = mc_df.merge(comp_df, on="company_id", how="left").merge(sec_df, on="company_id", how="left")
        return merged
    return mc_df


@st.cache_data(ttl=600)
def get_documents(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return annual report documents with BSE links."""
    conn = _get_connection()
    if ticker:
        query = "SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    else:
        query = "SELECT * FROM documents ORDER BY company_id ASC, year DESC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_prosandcons(ticker: Optional[str] = None) -> pd.DataFrame:
    """Return pros and cons qualitative analysis for a company or all companies."""
    conn = _get_connection()
    if ticker:
        query = "SELECT * FROM prosandcons WHERE company_id = ?"
        df = pd.read_sql_query(query, conn, params=(ticker,))
    else:
        query = "SELECT * FROM prosandcons"
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df
