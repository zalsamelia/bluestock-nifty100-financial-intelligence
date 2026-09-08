"""
Sector Analysis View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import get_sectors, get_ratios, get_valuation, get_pl
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout


def render_sectors_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Macro Industry Landscape</div>
            <div class="bento-hero-title">Sector Dynamics & Cross-Industry Benchmarks</div>
            <div class="bento-hero-sub">
                Comparative analysis of profitability, capital intensity, size dispersion, and median quality rankings across 11 Nifty 100 industry sectors.
            </div>
        </div>
    """, unsafe_allow_html=True)

    sectors_df = get_sectors()
    all_sectors = sorted(sectors_df["sector"].dropna().unique().tolist())

    selected_sector = st.selectbox(
        "Filter Broad Sector (11 Sectors):",
        options=["All Sectors"] + all_sectors,
        index=0,
        key="sectors_dropdown_filter"
    )

    ratios_2024 = get_ratios(year=2024)
    val_df = get_valuation()
    pl_2024 = get_pl()
    if not pl_2024.empty and "year" in pl_2024.columns:
        pl_2024 = pl_2024[pl_2024["year"] == 2024][["company_id", "sales", "net_profit"]]

    sector_data = ratios_2024.merge(pl_2024, on="company_id", how="left")
    if not val_df.empty:
        val_latest = val_df[val_df["year"] == 2024] if "year" in val_df.columns else val_df
        sector_data = sector_data.merge(
            val_latest[["company_id", "market_cap_crore", "pe_ratio"]],
            on="company_id",
            how="left"
        )

    if selected_sector != "All Sectors":
        sector_data = sector_data[sector_data["sector"] == selected_sector]

    sector_data["market_cap_crore"] = sector_data["market_cap_crore"].fillna(1000.0)
    sector_data["sales"] = sector_data["sales"].fillna(500.0)
    sector_data["return_on_equity_pct"] = sector_data["return_on_equity_pct"].fillna(0.0)

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Industry Landscape: Annual Sales vs ROE % (Bubble Size = Market Cap)</span>
            <span class="section-bar-tag">Capital Scale & Efficiency Map</span>
        </div>
    """, unsafe_allow_html=True)

    SECTOR_PALETTE = [
        "#00D294", "#F59E0B", "#38BDF8", "#818CF8", "#F43F5E",
        "#2DD4BF", "#FB923C", "#A78BFA", "#34D399", "#FBBF24", "#60A5FA"
    ]

    color_col = "industry" if selected_sector != "All Sectors" and "industry" in sector_data.columns else "sector"

    fig_bubble = px.scatter(
        sector_data,
        x="sales",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color=color_col,
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "sector": True,
            "industry": True,
            "sales": ":,.0f",
            "return_on_equity_pct": ":.1f",
            "market_cap_crore": ":,.0f",
            "pe_ratio": ":.1f"
        },
        labels={
            "sales": "Annual Sales (INR Crore)",
            "return_on_equity_pct": "Return on Equity (ROE %)",
            "market_cap_crore": "Market Cap (Cr)",
            "sector": "Sector",
            "industry": "Industry"
        },
        color_discrete_sequence=SECTOR_PALETTE
    )
    fig_bubble.update_layout(
        get_plotly_bento_layout(height=450),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#F8FAFC", family="IBM Plex Sans")
        ),
        margin=dict(l=45, r=30, t=30, b=80)
    )
    fig_bubble.update_traces(
        marker=dict(line=dict(width=0.5, color="rgba(8,14,17,0.25)"), opacity=0.85),
        hovertemplate="<b>%{hovertext}</b> (%{customdata[0]})<br>"
                      "<b>Sector:</b> %{customdata[1]} | <b>Industry:</b> %{customdata[2]}<br>"
                      "<b>Sales:</b> ₹%{x:,.0f} Cr | <b>ROE:</b> %{y:.1f}%<br>"
                      "<b>Market Cap:</b> ₹%{customdata[5]:,.0f} Cr | <b>P/E:</b> %{customdata[6]:.1f}x<extra></extra>"
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Cross-Sector Median KPI Benchmark Rankings</span>
            <span class="section-bar-tag">11-Sector Comparison</span>
        </div>
    """, unsafe_allow_html=True)

    all_sector_grouped = ratios_2024.groupby("sector").agg({
        "return_on_equity_pct": "median",
        "roce_pct": "median",
        "operating_profit_margin_pct": "median",
        "debt_to_equity": "median",
        "composite_quality_score": "median"
    }).reset_index()

    kpi_choice = st.selectbox(
        "Benchmark Metric:",
        options=[
            "Median ROE %",
            "Median ROCE %",
            "Median Operating Margin %",
            "Median Debt to Equity",
            "Median Quality Score"
        ],
        index=0,
        key="sectors_benchmark_metric"
    )

    metric_map = {
        "Median ROE %": "return_on_equity_pct",
        "Median ROCE %": "roce_pct",
        "Median Operating Margin %": "operating_profit_margin_pct",
        "Median Debt to Equity": "debt_to_equity",
        "Median Quality Score": "composite_quality_score"
    }

    target_col = metric_map[kpi_choice]
    all_sector_grouped = all_sector_grouped.sort_values(by=target_col, ascending=False)

    fig_bar = px.bar(
        all_sector_grouped,
        x="sector",
        y=target_col,
        labels={"sector": "Sector", target_col: kpi_choice},
        color=target_col,
        color_continuous_scale=[[0, "#1F2E3D"], [0.5, "#F59E0B"], [1.0, "#00D294"]]
    )
    fig_bar.update_layout(get_plotly_bento_layout(height=360))
    fig_bar.update_traces(marker_line_width=0)
    st.plotly_chart(fig_bar, use_container_width=True)
