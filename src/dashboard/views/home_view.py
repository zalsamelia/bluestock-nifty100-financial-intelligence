"""
Market Overview View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.utils.db import get_ratios, get_sectors, get_valuation, get_pl
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout


def render_home_view():
    # Live Market Ticker Ribbon
    ratios_2024 = get_ratios(year=2024)
    ticker_items = []
    if not ratios_2024.empty:
        sample_tickers = ["TCS", "INFY", "HDFCBANK", "ICICIBANK", "RELIANCE", "ITC", "LT", "BHARTIARTL", "HINDUNILVR", "TATAMOTORS"]
        ribbon_subset = ratios_2024[ratios_2024["company_id"].isin(sample_tickers)]
        for _, row in ribbon_subset.iterrows():
            t = row["company_id"]
            roe_val = row.get("return_on_equity_pct", 0.0)
            score_val = row.get("composite_quality_score", 50.0)
            ticker_items.append(
                f'<div class="ticker-item"><span class="ticker-symbol">{t}</span>'
                f'<span class="ticker-val">ROE:</span><span class="ticker-pos">{roe_val:.1f}%</span>'
                f'<span class="ticker-val">Score:</span><span class="ticker-pos">{score_val:.0f}</span></div>'
            )
    
    ribbon_html = f"""
        <div class="ticker-ribbon">
            <div style="font-family: 'JetBrains Mono'; font-size: 0.72rem; font-weight: 800; color: #00D294; display: flex; align-items: center;">
                <span class="live-pulse"></span>BLUESTOCK FEED:
            </div>
            {" ".join(ticker_items)}
        </div>
    """
    st.markdown(ribbon_html, unsafe_allow_html=True)

    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Macro Market Intelligence</div>
            <div class="bento-hero-title">Nifty 100 Fundamental Baseline & Quality Matrix</div>
            <div class="bento-hero-sub">
                Institutional fundamental telemetry across 92 elite Nifty 100 corporate constituents. Real-time valuation dispersion, capital efficiency benchmarks, and quality score leadership.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Filter Controls Bar
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        selected_year = st.selectbox(
            "Fiscal Baseline:",
            options=[2024, 2023, 2022, 2021, 2020, 2019],
            index=0,
            key="home_year_select"
        )
    with f_col2:
        sectors_all = get_sectors()
        sec_list = ["All Sectors (11)"] + sorted(sectors_all["sector"].dropna().unique().tolist()) if not sectors_all.empty else ["All Sectors"]
        selected_sec = st.selectbox(
            "Sector Filter:",
            options=sec_list,
            index=0,
            key="home_sec_filter"
        )

    ratios_df = get_ratios(year=selected_year)
    val_df = get_valuation()
    val_year = val_df[val_df["year"] == selected_year] if not val_df.empty and "year" in val_df.columns else val_df

    if selected_sec != "All Sectors (11)" and "sector" in ratios_df.columns:
        ratios_df = ratios_df[ratios_df["sector"] == selected_sec]
        if not val_year.empty and "sector" in val_year.columns:
            val_year = val_year[val_year["sector"] == selected_sec]

    # Aggregate Top Level Numbers
    avg_roe = ratios_df["return_on_equity_pct"].mean() if not ratios_df.empty else 0.0
    median_pe = val_year["pe_ratio"].median() if not val_year.empty and "pe_ratio" in val_year.columns else 0.0
    median_de = ratios_df["debt_to_equity"].median() if not ratios_df.empty else 0.0
    total_companies = len(ratios_df["company_id"].unique()) if not ratios_df.empty else 0
    median_rev_cagr = ratios_df["revenue_cagr_5yr"].median() if not ratios_df.empty else 0.0
    # Debt-Free Companies = D/E ratio of 0 or negative (effectively zero debt)
    debt_free_count = int((ratios_df["debt_to_equity"] <= 0.05).sum()) if not ratios_df.empty and "debt_to_equity" in ratios_df.columns else 0

    # 6 Top Bento Stat Tiles (as per Sprint 4 spec)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Average ROE</div>
                <div class="bento-stat-val" style="color: #00D294;">{avg_roe:.1f}%</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">Universe Mean</span></div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="bento-card bento-card-gold">
                <div class="bento-stat-label">Median P/E Multiple</div>
                <div class="bento-stat-val" style="color: #F59E0B;">{median_pe:.1f}x</div>
                <div class="bento-stat-sub"><span class="bento-badge-gold">Sector Median</span></div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Median D/E Ratio</div>
                <div class="bento-stat-val">{median_de:.2f}</div>
                <div class="bento-stat-sub"><span class="bento-badge-slate">Leverage Index</span></div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Coverage Universe</div>
                <div class="bento-stat-val" style="color: #38BDF8;">{total_companies}</div>
                <div class="bento-stat-sub"><span class="bento-badge-slate">Active Constituents</span></div>
            </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">5-Yr Revenue CAGR</div>
                <div class="bento-stat-val" style="color: #00D294;">{median_rev_cagr:.1f}%</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">Median Growth</span></div>
            </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
            <div class="bento-card" style="border-top: 3px solid #00D294;">
                <div class="bento-stat-label">Debt-Free Companies</div>
                <div class="bento-stat-val" style="color: #00D294;">{debt_free_count}</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">D/E &le; 0.05</span></div>
            </div>
        """, unsafe_allow_html=True)


    # Primary Analytics View: 2-Column Section: Sector Breakdown + Top Quality Leaders
    r_col1, r_col2 = st.columns([1, 1])

    with r_col1:
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">Sector Composition & Weight Distribution</span>
                <span class="section-bar-tag">11 Industry Sectors</span>
            </div>
        """, unsafe_allow_html=True)
        sectors_df = get_sectors()
        if not sectors_df.empty:
            sec_counts = sectors_df["sector"].value_counts().reset_index()
            sec_counts.columns = ["Sector", "Companies"]

            SECTOR_PALETTE = [
                "#00D294", "#F59E0B", "#38BDF8", "#818CF8", "#F43F5E",
                "#2DD4BF", "#FB923C", "#A78BFA", "#34D399", "#FBBF24", "#60A5FA"
            ]

            fig = px.pie(
                sec_counts,
                names="Sector",
                values="Companies",
                hole=0.55,
                color_discrete_sequence=SECTOR_PALETTE
            )
            fig.update_layout(
                get_plotly_bento_layout(height=390),
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(color="#FFFFFF", family="IBM Plex Sans", size=11)
                ),
                margin=dict(l=20, r=120, t=30, b=30)
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                insidetextfont=dict(color="#FFFFFF", family="JetBrains Mono", size=10),
                marker=dict(line=dict(color="rgba(8,14,17,0.35)", width=1)),
                hovertemplate="<b>%{label}</b><br>Count: %{value} companies<br>Weight: %{percent}<extra></extra>",
                pull=[0.02] * len(sec_counts)
            )
            st.plotly_chart(fig, use_container_width=True)

    with r_col2:
        st.markdown(f"""
            <div class="section-bar">
                <span class="section-bar-title">Top 5 Quality Alpha Champions (FY{selected_year})</span>
                <span class="section-bar-tag">Highest Fundamental Rank</span>
            </div>
        """, unsafe_allow_html=True)
        if not ratios_df.empty and "composite_quality_score" in ratios_df.columns:
            top5 = ratios_df.sort_values(by="composite_quality_score", ascending=False).head(5)
            display_cols = ["company_id", "company_name", "sector", "composite_quality_score", "return_on_equity_pct", "debt_to_equity"]
            avail_cols = [c for c in display_cols if c in top5.columns]
            top5_table = top5[avail_cols].copy()
            
            rename_map = {
                "company_id": "Ticker",
                "company_name": "Company Name",
                "sector": "Sector",
                "composite_quality_score": "Quality Score",
                "return_on_equity_pct": "ROE %",
                "debt_to_equity": "D/E"
            }
            top5_table = top5_table.rename(columns=rename_map)
            
            st.dataframe(
                top5_table.style.format({
                    "Quality Score": "{:.1f}",
                    "ROE %": "{:.1f}%",
                    "D/E": "{:.2f}"
                }, na_rep="N/A"),
                hide_index=True,
                use_container_width=True,
                height=390
            )

    # Secondary Bento Row: Quality Score Distribution & Valuation Dispersal
    sec_c1, sec_c2 = st.columns([1, 1])
    with sec_c1:
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">Universe Quality Score Dispersal</span>
                <span class="section-bar-tag">Histogram</span>
            </div>
        """, unsafe_allow_html=True)
        if not ratios_df.empty and "composite_quality_score" in ratios_df.columns:
            fig_hist = px.histogram(
                ratios_df,
                x="composite_quality_score",
                nbins=16,
                color_discrete_sequence=["#00D294"],
                labels={"composite_quality_score": "Composite Quality Score (0-100)"}
            )
            fig_hist.update_layout(get_plotly_bento_layout(height=280), bargap=0.05)
            fig_hist.update_traces(marker_line_width=0)
            st.plotly_chart(fig_hist, use_container_width=True)

    with sec_c2:
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">Valuation vs Return on Equity</span>
                <span class="section-bar-tag">P/E vs ROE</span>
            </div>
        """, unsafe_allow_html=True)
        if not ratios_df.empty and not val_year.empty:
            merged_scatter = ratios_df.merge(val_year[["company_id", "pe_ratio"]], on="company_id", how="inner")
            merged_scatter = merged_scatter[merged_scatter["pe_ratio"] > 0]
            if not merged_scatter.empty:
                fig_scat = px.scatter(
                    merged_scatter,
                    x="pe_ratio",
                    y="return_on_equity_pct",
                    color="sector" if "sector" in merged_scatter.columns else None,
                    hover_name="company_name",
                    hover_data={"company_id": True, "pe_ratio": ":.1f", "return_on_equity_pct": ":.1f%"},
                    labels={"pe_ratio": "P/E Multiple (x)", "return_on_equity_pct": "ROE %"},
                    color_discrete_sequence=PALETTE["chart_series"]
                )
                fig_scat.update_layout(get_plotly_bento_layout(height=280))
                st.plotly_chart(fig_scat, use_container_width=True)
