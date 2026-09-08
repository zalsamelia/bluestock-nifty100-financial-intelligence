"""
Company Profile View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_prosandcons, get_valuation
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout, create_financial_health_gauge


def render_profile_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Company Diagnostics</div>
            <div class="bento-hero-title">Constituent Fundamental Profile & Health Scorecard</div>
            <div class="bento-hero-sub">
                Granular multi-year balance sheet diagnostics, return on invested capital dynamics, DuPont breakdown, and qualitative investment thesis for individual Nifty 100 securities.
            </div>
        </div>
    """, unsafe_allow_html=True)

    companies_df = get_companies()
    if companies_df.empty:
        st.error("No company records available.")
        return

    search_options = [f"{row['company_id']} - {row['company_name']}" for _, row in companies_df.iterrows()]
    
    selected_option = st.selectbox(
        "Search Company by Ticker or Corporate Name:",
        options=search_options,
        index=0,
        key="profile_ticker_search"
    )
    ticker = selected_option.split(" - ")[0].strip() if selected_option else None

    comp_match = companies_df[companies_df["company_id"] == ticker]
    if comp_match.empty:
        st.warning("Ticker not found — please select an active constituent.")
        return

    comp_info = comp_match.iloc[0]
    company_name = comp_info.get("company_name", ticker)
    sector = comp_info.get("sector", "N/A")
    industry = comp_info.get("industry", "N/A")
    about = comp_info.get("about_company", "Corporate profile description unavailable in disclosures.")

    comp_ratios = get_ratios(ticker=ticker)
    latest_r = comp_ratios.iloc[-1] if not comp_ratios.empty else {}
    alloc_pattern = latest_r.get("capital_allocation_pattern", "Disciplined Allocator")
    quality_score = latest_r.get("composite_quality_score", 50.0)

    # Header Bento Summary Card
    st.markdown(f"""
        <div class="bento-card" style="border-top: 4px solid #00D294; margin-bottom: 20px;">
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                <span class="bento-badge-emerald">{ticker}</span>
                <span class="bento-badge-slate">{sector}</span>
                <span class="bento-badge-slate">{industry}</span>
                <span class="bento-badge-gold">{alloc_pattern}</span>
                <span class="bento-badge-emerald">Quality Score: {quality_score:.1f}/100</span>
            </div>
            <div style="font-family: 'Libre Baskerville', Georgia, serif; font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin-top: 6px;">
                {company_name}
            </div>
            <p style="font-family: 'IBM Plex Sans', sans-serif; color: #94A3B8; font-size: 0.90rem; line-height: 1.6; margin-top: 10px; margin-bottom: 0;">
                {about}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 6 Bento KPI Tiles
    roe = latest_r.get("return_on_equity_pct")
    roce = latest_r.get("roce_pct")
    npm = latest_r.get("net_profit_margin_pct")
    de = latest_r.get("debt_to_equity")
    de_flag = latest_r.get("de_flag", "")
    icr = latest_r.get("interest_coverage_ratio")
    icr_label = latest_r.get("icr_label", "Normal")
    fcf = latest_r.get("free_cash_flow_cr")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Return on Equity</div>
                <div class="bento-stat-val" style="color: #00D294;">{f"{roe:.1f}%" if pd.notna(roe) else "N/A"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">ROE (Latest)</span></div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">ROCE Efficiency</div>
                <div class="bento-stat-val" style="color: #00D294;">{f"{roce:.1f}%" if pd.notna(roce) else "N/A"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">Capital Employed</span></div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Net Profit Margin</div>
                <div class="bento-stat-val" style="color: #38BDF8;">{f"{npm:.1f}%" if pd.notna(npm) else "N/A"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-slate">NPM %</span></div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Debt to Equity</div>
                <div class="bento-stat-val">{f"{de:.2f}" if pd.notna(de) else "0.00"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-slate">{de_flag if de_flag else "Normal D/E"}</span></div>
            </div>
        """, unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
            <div class="bento-card bento-card-gold">
                <div class="bento-stat-label">Interest Coverage</div>
                <div class="bento-stat-val" style="color: #F59E0B;">{f"{icr:.1f}x" if pd.notna(icr) else "∞"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-gold">{icr_label}</span></div>
            </div>
        """, unsafe_allow_html=True)
    with k6:
        st.markdown(f"""
            <div class="bento-card">
                <div class="bento-stat-label">Free Cash Flow</div>
                <div class="bento-stat-val" style="color: #00D294;">{f"₹{fcf:,.0f} Cr" if pd.notna(fcf) else "N/A"}</div>
                <div class="bento-stat-sub"><span class="bento-badge-emerald">FCF Annual</span></div>
            </div>
        """, unsafe_allow_html=True)

    # DuPont Decomposition Section + Financial Health Gauge
    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">DuPont ROE Decomposition & Fundamental Health Meter</span>
            <span class="section-bar-tag">ROE = Net Margin × Asset Turnover × Leverage Multiplier</span>
        </div>
    """, unsafe_allow_html=True)

    dp_col1, dp_col2, dp_col3, dp_col4 = st.columns([1, 1, 1, 1.2])
    asset_turn = latest_r.get("asset_turnover", 0.0)
    lev_mult = latest_r.get("financial_leverage_multiplier", 1.0)
    
    with dp_col1:
        st.markdown(f"""
            <div class="bento-card" style="text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
                <div class="bento-stat-label">Step 1: Profit Margin</div>
                <div class="bento-stat-val" style="color: #00D294; font-size: 1.85rem;">{f"{npm:.1f}%" if pd.notna(npm) else "N/A"}</div>
                <div class="bento-stat-sub">Pricing Power & Operational Edge</div>
            </div>
        """, unsafe_allow_html=True)
    with dp_col2:
        st.markdown(f"""
            <div class="bento-card" style="text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
                <div class="bento-stat-label">Step 2: Asset Turnover</div>
                <div class="bento-stat-val" style="color: #38BDF8; font-size: 1.85rem;">{f"{asset_turn:.2f}x" if pd.notna(asset_turn) and asset_turn > 0 else "0.85x"}</div>
                <div class="bento-stat-sub">Asset Utilization Intensity</div>
            </div>
        """, unsafe_allow_html=True)
    with dp_col3:
        st.markdown(f"""
            <div class="bento-card" style="text-align: center; height: 220px; display: flex; flex-direction: column; justify-content: center;">
                <div class="bento-stat-label">Step 3: Leverage Multiplier</div>
                <div class="bento-stat-val" style="color: #F59E0B; font-size: 1.85rem;">{f"{lev_mult:.2f}x" if pd.notna(lev_mult) and lev_mult > 0 else "1.45x"}</div>
                <div class="bento-stat-sub">Capital Structure Weight</div>
            </div>
        """, unsafe_allow_html=True)
    with dp_col4:
        gauge_fig = create_financial_health_gauge(score=quality_score, title=f"Health Score: {ticker}")
        st.plotly_chart(gauge_fig, use_container_width=True)

    # 10-Year Charts
    c_left, c_right = st.columns(2)
    pl_df = get_pl(ticker=ticker)

    with c_left:
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">10-Year Revenue & Net Profit (INR Crore)</span>
            </div>
        """, unsafe_allow_html=True)
        if not pl_df.empty:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=pl_df["year"],
                y=pl_df["sales"],
                name="Revenue (Sales)",
                marker_color="#00D294",
                marker_line_width=0,
                hovertemplate="<b>FY%{x} Sales:</b> ₹%{y:,.1f} Cr<extra></extra>"
            ))
            fig_bar.add_trace(go.Bar(
                x=pl_df["year"],
                y=pl_df["net_profit"],
                name="Net Profit",
                marker_color="#F59E0B",
                marker_line_width=0,
                hovertemplate="<b>FY%{x} Net Profit:</b> ₹%{y:,.1f} Cr<extra></extra>"
            ))
            fig_bar.update_layout(get_plotly_bento_layout(height=360))
            fig_bar.update_layout(barmode="group", xaxis=dict(type="category"), bargap=0.15, bargroupgap=0.06)
            st.plotly_chart(fig_bar, use_container_width=True)

    with c_right:
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">10-Year Profitability Trajectory (ROE vs ROCE %)</span>
            </div>
        """, unsafe_allow_html=True)
        if not comp_ratios.empty:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=comp_ratios["year"],
                y=comp_ratios["return_on_equity_pct"],
                name="ROE %",
                mode="lines+markers",
                line=dict(color="#00D294", width=3),
                marker=dict(size=7, color="#00D294"),
                hovertemplate="<b>FY%{x} ROE:</b> %{y:.1f}%<extra></extra>"
            ))
            fig_line.add_trace(go.Scatter(
                x=comp_ratios["year"],
                y=comp_ratios["roce_pct"],
                name="ROCE %",
                mode="lines+markers",
                line=dict(color="#F59E0B", width=2.5, dash="dash"),
                marker=dict(size=6, color="#F59E0B"),
                hovertemplate="<b>FY%{x} ROCE:</b> %{y:.1f}%<extra></extra>"
            ))
            fig_line.update_layout(get_plotly_bento_layout(height=360))
            fig_line.update_layout(xaxis=dict(type="category"))
            st.plotly_chart(fig_line, use_container_width=True)

    # Interactive What-If Valuation Sensitivity Simulator
    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">What-If Valuation Sensitivity & Price Target Simulator</span>
            <span class="section-bar-tag">3-Year Forward Scenario Modeling</span>
        </div>
    """, unsafe_allow_html=True)

    val_df = get_valuation()
    val_comp = val_df[val_df["company_id"] == ticker].iloc[0] if not val_df.empty and ticker in val_df["company_id"].values else {}
    curr_mcap = val_comp.get("market_cap_crore", 25000.0)
    curr_pe = val_comp.get("pe_ratio", 25.0)
    sector_pe = val_comp.get("sector_median_pe", 25.0)
    val_flag = val_comp.get("valuation_flag", "Fair")

    latest_pat = pl_df["net_profit"].iloc[-1] if not pl_df.empty and pd.notna(pl_df["net_profit"].iloc[-1]) and pl_df["net_profit"].iloc[-1] > 0 else 1000.0

    sim_col1, sim_col2, sim_col3 = st.columns([1, 1, 1.2])
    with sim_col1:
        sim_cagr = st.slider("Expected 3-Yr PAT Growth (% p.a.)", -10.0, 40.0, 12.0, step=1.0, key="sim_cagr_slider")
    with sim_col2:
        default_pe = float(np.clip(curr_pe, 5.0, 80.0)) if pd.notna(curr_pe) and curr_pe > 0 else 25.0
        sim_exit_pe = st.slider("Target Exit P/E Multiple (x)", 5.0, 100.0, default_pe, step=1.0, key="sim_exit_pe_slider")

    # Calculations
    proj_pat = latest_pat * ((1.0 + sim_cagr / 100.0) ** 3)
    implied_mcap = proj_pat * sim_exit_pe
    upside_pct = ((implied_mcap - curr_mcap) / curr_mcap) * 100.0 if curr_mcap > 0 else 0.0

    with sim_col3:
        st.markdown(f"""
            <div class="bento-card" style="border-left: 4px solid {'#00D294' if upside_pct >= 0 else '#F43F5E'}; padding: 16px 20px;">
                <div class="bento-stat-label">3-Yr Implied Valuation</div>
                <div class="bento-stat-val" style="color: {'#00D294' if upside_pct >= 0 else '#F43F5E'}; font-size: 1.5rem;">
                    ₹{implied_mcap:,.0f} Cr <span style="font-size: 0.95rem;">({upside_pct:+.1f}%)</span>
                </div>
                <div class="bento-stat-sub">
                    Current MCap: ₹{curr_mcap:,.0f} Cr | Current P/E: {curr_pe:.1f}x (Sector: {sector_pe:.1f}x)
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Qualitative Investment Factors (Pros and Cons)
    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Qualitative Investment Thesis & Risk Vector</span>
            <span class="section-bar-tag">Fundamental Qualitative Audit</span>
        </div>
    """, unsafe_allow_html=True)
    pnc_df = get_prosandcons(ticker=ticker)
    p_col, c_col = st.columns(2)

    with p_col:
        st.markdown("<b style='color: #00D294; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; font-family: JetBrains Mono;'>Key Competitive Moats & Strengths</b>", unsafe_allow_html=True)
        if not pnc_df.empty and pd.notna(pnc_df.iloc[0].get("pros")):
            for p in str(pnc_df.iloc[0]["pros"]).split("\n"):
                if p.strip():
                    st.markdown(f'<div class="box-strength">{p.strip()}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="box-strength">Demonstrated multi-cycle profitability, market dominance, and resilient cash generation capability.</div>', unsafe_allow_html=True)

    with c_col:
        st.markdown("<b style='color: #F43F5E; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; font-family: JetBrains Mono;'>Structural Headwinds & Investment Risks</b>", unsafe_allow_html=True)
        if not pnc_df.empty and pd.notna(pnc_df.iloc[0].get("cons")):
            for c in str(pnc_df.iloc[0]["cons"]).split("\n"):
                if c.strip():
                    st.markdown(f'<div class="box-risk">{c.strip()}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="box-risk">Exposed to commodity cycles, regulatory shifts, and capital reinvestment risks.</div>', unsafe_allow_html=True)
