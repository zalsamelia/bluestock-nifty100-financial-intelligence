"""
Capital Allocation Map View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from src.dashboard.utils.db import get_ratios, get_valuation
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout


def render_capital_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Capital Allocation Strategy</div>
            <div class="bento-hero-title">Capital Allocation Taxonomy (8 Archetypes)</div>
            <div class="bento-hero-sub">
                Structural corporate capital deployment framework: Reinvestment intensity, operating cash flow quality, debt discipline, and shareholder yield patterns across the Nifty 100 universe.
            </div>
        </div>
    """, unsafe_allow_html=True)

    ratios_df = get_ratios(year=2024)
    val_df = get_valuation()
    if not val_df.empty:
        val_2024 = val_df[val_df["year"] == 2024] if "year" in val_df.columns else val_df
        ratios_df = ratios_df.merge(
            val_2024[["company_id", "market_cap_crore"]],
            on="company_id",
            how="left"
        )

    ratios_df["market_cap_crore"] = ratios_df["market_cap_crore"].fillna(5000.0)
    ratios_df["capital_allocation_pattern"] = ratios_df["capital_allocation_pattern"].fillna("Disciplined Allocator")

    ARCHETYPE_COLORS = {
        "Shareholder Returns": "#00D294",          # Mint Emerald (Rewarding shareholders)
        "Reinvestor": "#0D9488",                   # Deep Teal (Compounding reinvestment)
        "Growth Funded by Operations": "#10B981",  # Fresh Jade (Clean organic cashflow growth)
        "Growth Funded by Debt": "#F59E0B",        # Sovereign Amber Gold (Leveraged growth)
        "Mixed": "#6366F1",                        # Slate Indigo (Balanced allocation)
        "Asset Heavy": "#38BDF8",                  # Sky Cyan (Capital intensive industrial)
        "Liquidating Assets": "#E11D48",           # Crimson Rose (Restructuring/divestment)
        "Pre-Revenue": "#8B5CF6",                  # Modern Violet (Early stage/incubating)
        "Disciplined Allocator": "#059669",        # Deep Forest Jade
    }

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Universe Treemap: 8 Capital Allocation Archetypes</span>
            <span class="section-bar-tag">Weighted by Market Capitalization (INR Cr)</span>
        </div>
    """, unsafe_allow_html=True)

    fig_tree = px.treemap(
        ratios_df,
        path=["capital_allocation_pattern", "sector", "company_id"],
        values="market_cap_crore",
        color="capital_allocation_pattern",
        hover_name="company_name",
        hover_data={
            "return_on_equity_pct": ":.1f",
            "debt_to_equity": ":.2f",
            "free_cash_flow_cr": ":,.0f"
        },
        color_discrete_map=ARCHETYPE_COLORS
    )
    fig_tree.update_layout(
        get_plotly_bento_layout(height=500),
        margin=dict(l=0, r=0, t=10, b=0)
    )
    fig_tree.update_traces(
        textinfo="label+value",
        textfont=dict(family="IBM Plex Sans, sans-serif", size=11, color="#FFFFFF"),
        marker=dict(
            cornerradius=4,
            pad=dict(t=18, l=3, r=3, b=3),
            line=dict(width=0.5, color="rgba(8,14,17,0.4)")
        ),
        hovertemplate="<b>%{label}</b><br>Market Cap: ₹%{value:,.0f} Cr<extra></extra>"
    )
    st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Pattern Breakdown & Constituent Registry</span>
            <span class="section-bar-tag">Granular Capital Quality Drill-Down</span>
        </div>
    """, unsafe_allow_html=True)

    pattern_options = ["All Patterns"] + sorted(ratios_df["capital_allocation_pattern"].unique().tolist())
    selected_pattern = st.selectbox(
        "Filter Pattern Archetype:",
        options=pattern_options,
        index=0,
        key="capital_pattern_select"
    )

    drill_df = ratios_df if selected_pattern == "All Patterns" else ratios_df[ratios_df["capital_allocation_pattern"] == selected_pattern]

    disp_cols = [
        "company_id", "company_name", "sector", "capital_allocation_pattern",
        "cfo_quality_label", "capex_intensity_label", "fcf_conversion_pct",
        "return_on_equity_pct", "debt_to_equity"
    ]
    avail = [c for c in disp_cols if c in drill_df.columns]
    tbl = drill_df[avail].copy()

    st.dataframe(
        tbl.rename(columns={
            "company_id": "Ticker",
            "company_name": "Company Name",
            "sector": "Sector",
            "capital_allocation_pattern": "Allocation Archetype",
            "cfo_quality_label": "CFO Quality",
            "capex_intensity_label": "CapEx Intensity",
            "fcf_conversion_pct": "FCF Conversion %",
            "return_on_equity_pct": "ROE %",
            "debt_to_equity": "D/E"
        }).style.format({
            "FCF Conversion %": "{:.1f}%",
            "ROE %": "{:.1f}%",
            "D/E": "{:.2f}"
        }, na_rep="N/A"),
        hide_index=True,
        use_container_width=True,
        height=380
    )
