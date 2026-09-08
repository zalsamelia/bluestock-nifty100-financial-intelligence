"""
Trend Analysis View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios, get_pl
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout


def render_trends_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Longitudinal Performance</div>
            <div class="bento-hero-title">10-Year Financial Trajectory & Trend Analysis</div>
            <div class="bento-hero-sub">
                Multi-metric historical trajectory tracking, revenue-to-profit conversion, and year-over-year rate of change annotations across 14 fiscal horizons.
            </div>
        </div>
    """, unsafe_allow_html=True)

    companies_df = get_companies()
    search_options = [f"{row['company_id']} - {row['company_name']}" for _, row in companies_df.iterrows()]

    col_search, col_metrics = st.columns([1, 2])

    with col_search:
        selected_option = st.selectbox(
            "Select Constituent Company:",
            options=search_options,
            index=0,
            key="trends_comp_search"
        )
        ticker = selected_option.split(" - ")[0].strip()

    available_metrics = {
        "Revenue (Sales)": "sales",
        "Net Profit": "net_profit",
        "Operating Profit": "operating_profit",
        "Return on Equity (ROE %)": "return_on_equity_pct",
        "Return on Capital (ROCE %)": "roce_pct",
        "Operating Margin (OPM %)": "operating_profit_margin_pct",
        "Net Profit Margin (NPM %)": "net_profit_margin_pct",
        "Debt to Equity (D/E)": "debt_to_equity",
        "Free Cash Flow (Cr)": "free_cash_flow_cr",
        "Earnings Per Share (EPS)": "earnings_per_share"
    }

    with col_metrics:
        selected_metric_names = st.multiselect(
            "Select Metrics to Overlay (Max 3):",
            options=list(available_metrics.keys()),
            default=["Revenue (Sales)", "Net Profit"],
            max_selections=3,
            key="trends_metric_multiselect"
        )

    if not selected_metric_names:
        st.warning("Select at least one metric to display trajectory analysis.")
        return

    ratios_ts = get_ratios(ticker=ticker)
    pl_ts = get_pl(ticker=ticker)
    merged_ts = pl_ts.merge(ratios_ts, on=["company_id", "year"], how="outer").sort_values("year").reset_index(drop=True)

    if merged_ts.empty:
        st.info("No time series records available for the selected security.")
        return

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">10-Year Multi-Metric Trend Trajectory</span>
            <span class="section-bar-tag">With YoY Rate of Change Deliberation</span>
        </div>
    """, unsafe_allow_html=True)

    from plotly.subplots import make_subplots

    currency_keys = ["sales", "net_profit", "operating_profit", "free_cash_flow_cr"]
    has_currency = any(available_metrics[m] in currency_keys for m in selected_metric_names)
    has_ratio = any(available_metrics[m] not in currency_keys for m in selected_metric_names)
    use_dual_axis = has_currency and has_ratio

    if use_dual_axis:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig = go.Figure()

    for idx, m_name in enumerate(selected_metric_names):
        col_key = available_metrics[m_name]
        if col_key not in merged_ts.columns:
            continue

        series = pd.to_numeric(merged_ts[col_key], errors="coerce")
        years = merged_ts["year"]
        yoy_pct = series.pct_change() * 100.0
        color = PALETTE["chart_series"][idx % len(PALETTE["chart_series"])]
        is_curr = col_key in currency_keys

        hover_texts = []
        for y, val, pct in zip(years, series, yoy_pct):
            pct_str = f" ({pct:+.1f}% YoY)" if pd.notna(pct) else " (Base Year)"
            if pd.isna(val) or val is None:
                val_str = "N/A"
            elif is_curr:
                val_str = f"₹{val:,.1f} Cr"
            elif "pct" in col_key or "margin" in col_key or "roe" in col_key or "roce" in col_key:
                val_str = f"{val:.1f}%"
            else:
                val_str = f"{val:.2f}"
            hover_texts.append(f"<b>FY{y} {m_name}:</b> {val_str}{pct_str}")

        trace = go.Scatter(
            x=years,
            y=series,
            name=m_name,
            mode="lines+markers+text",
            text=[f"{pct:+.0f}%" if pd.notna(pct) and abs(pct) > 1 else "" for pct in yoy_pct],
            textposition="top center",
            textfont=dict(size=9, color=color, family="JetBrains Mono"),
            line=dict(color=color, width=2.8),
            marker=dict(size=7, color=color),
            hovertext=hover_texts,
            hoverinfo="text"
        )

        if use_dual_axis:
            fig.add_trace(trace, secondary_y=(not is_curr))
        else:
            fig.add_trace(trace)

    base_layout = get_plotly_bento_layout(title=f"Constituent Trajectory: {ticker} (FY{merged_ts['year'].min()} – FY{merged_ts['year'].max()})", height=450)
    fig.update_layout(base_layout)
    fig.update_layout(xaxis=dict(type="category"))
    
    if use_dual_axis:
        fig.update_yaxes(title_text="<b>Absolute Financials (INR Cr)</b>", secondary_y=False, showgrid=True, gridcolor="#1F2E3D")
        fig.update_yaxes(title_text="<b>Ratios & Percentages (%)</b>", secondary_y=True, showgrid=False)
        
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Tabular Longitudinal Financial Ledger</span>
            <span class="section-bar-tag">Annual Metric Comparison Matrix</span>
        </div>
    """, unsafe_allow_html=True)
    disp_cols = ["year"] + [available_metrics[m] for m in selected_metric_names if available_metrics[m] in merged_ts.columns]
    tbl = merged_ts[disp_cols].copy()
    tbl.columns = ["Fiscal Year"] + selected_metric_names
    
    # Format table values safely
    format_map = {}
    for col in selected_metric_names:
        c_key = available_metrics[col]
        if c_key in currency_keys:
            format_map[col] = "₹{:,.1f} Cr"
        elif "pct" in c_key or "margin" in c_key or "roe" in c_key or "roce" in c_key:
            format_map[col] = "{:.1f}%"
        else:
            format_map[col] = "{:.2f}"
            
    st.dataframe(tbl.set_index("Fiscal Year").T.style.format(format_map, na_rep="N/A"), use_container_width=True)
