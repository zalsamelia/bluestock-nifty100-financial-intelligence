"""
Peer Benchmark View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from src.dashboard.utils.db import get_peer_groups_list, get_peers, get_ratios, get_companies, get_valuation
from src.dashboard.utils.styles import PALETTE, get_plotly_bento_layout


def render_peers_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Peer Intelligence</div>
            <div class="bento-hero-title">Sector Peer Comparison & Head-to-Head Duel Matrix</div>
            <div class="bento-hero-sub">
                Multi-axial competitive benchmarking across 11 Nifty 100 industry peer groups. Evaluate intra-industry percentiles or perform direct pairwise head-to-head financial duels.
            </div>
        </div>
    """, unsafe_allow_html=True)

    peer_mode = st.radio(
        "Select Analytical Mode:",
        options=["1. Intra-Industry Peer Radar & Baseline", "2. Head-to-Head Constituent Duel Matrix"],
        horizontal=True,
        key="peer_view_mode_radio"
    )

    all_ratios = get_ratios(year=2024)

    if peer_mode == "1. Intra-Industry Peer Radar & Baseline":
        peer_groups = get_peer_groups_list()
        if not peer_groups:
            st.error("No peer groups found in intelligence database.")
            return

        sel_col1, sel_col2 = st.columns(2)
        with sel_col1:
            selected_group = st.selectbox(
                "Select Industry Peer Group (11 Groups):",
                options=peer_groups,
                index=peer_groups.index("IT Services") if "IT Services" in peer_groups else 0,
                key="peers_group_select"
            )

        group_peers = get_peers(group_name=selected_group)
        if group_peers.empty:
            st.warning(f"No constituents registered in {selected_group}.")
            return

        companies_in_group = group_peers["company_id"].unique().tolist()
        group_ratios = all_ratios[all_ratios["company_id"].isin(companies_in_group)].copy()

        with sel_col2:
            selected_ticker = st.selectbox(
                "Select Focal Constituent for Radar Analysis:",
                options=companies_in_group,
                index=0,
                key="peers_comp_select"
            )

        # Radar Chart
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">8-Axis Competitive Profile vs Peer Group Median</span>
                <span class="section-bar-tag">Normalized Percentile Radar (0-100)</span>
            </div>
        """, unsafe_allow_html=True)

        focus_data = group_ratios[group_ratios["company_id"] == selected_ticker]

        axes = [
            ("ROE %", "return_on_equity_pct", False),
            ("ROCE %", "roce_pct", False),
            ("NPM %", "net_profit_margin_pct", False),
            ("D/E (Inv)", "debt_to_equity", True),
            ("FCF (Cr)", "free_cash_flow_cr", False),
            ("PAT CAGR", "pat_cagr_5yr", False),
            ("Rev CAGR", "revenue_cagr_5yr", False),
            ("Quality Score", "composite_quality_score", False),
        ]

        labels = [a[0] for a in axes]
        comp_vals = []
        peer_avg_vals = []

        for label, col, invert in axes:
            if col in group_ratios.columns:
                s_min = group_ratios[col].min()
                s_max = group_ratios[col].max()
                span = s_max - s_min if s_max != s_min else 1.0

                c_raw = focus_data.iloc[0][col] if not focus_data.empty and col in focus_data.columns else s_min
                if pd.isna(c_raw):
                    c_raw = s_min
                c_norm = (c_raw - s_min) / span * 100.0
                if invert:
                    c_norm = 100.0 - c_norm
                comp_vals.append(c_norm)

                p_raw = group_ratios[col].mean()
                p_norm = (p_raw - s_min) / span * 100.0
                if invert:
                    p_norm = 100.0 - p_norm
                peer_avg_vals.append(p_norm)
            else:
                comp_vals.append(50.0)
                peer_avg_vals.append(50.0)

        labels_closed = labels + [labels[0]]
        comp_vals_closed = comp_vals + [comp_vals[0]]
        peer_avg_closed = peer_avg_vals + [peer_avg_vals[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=comp_vals_closed,
            theta=labels_closed,
            fill='toself',
            fillcolor='rgba(0, 210, 148, 0.22)',
            line=dict(color="#00D294", width=3),
            name=f"Focus: {selected_ticker}"
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=peer_avg_closed,
            theta=labels_closed,
            line=dict(color="#F59E0B", width=2.5, dash='dash'),
            name=f"{selected_group} Average"
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=9, color="#94A3B8", family="JetBrains Mono"),
                    gridcolor="#1F2E3D",
                    linecolor="#1F2E3D"
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color="#F8FAFC", family="IBM Plex Sans"),
                    gridcolor="#1F2E3D",
                    linecolor="#1F2E3D"
                ),
                bgcolor="#0C131D"
            ),
            showlegend=True,
            height=420,
            margin=dict(l=50, r=50, t=30, b=30),
            paper_bgcolor="#111A22",
            legend=dict(orientation="h", y=-0.1, x=0.25, font=dict(color="#CBD5E1", family="IBM Plex Sans"))
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Comparative Table
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">Peer Group Financial Baseline (FY2024)</span>
                <span class="section-bar-tag">Ranked by Composite Quality Score</span>
            </div>
        """, unsafe_allow_html=True)
        display_cols = [
            "company_id", "company_name", "composite_quality_score",
            "return_on_equity_pct", "roce_pct", "net_profit_margin_pct",
            "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr",
            "pat_cagr_5yr", "asset_turnover"
        ]
        avail = [c for c in display_cols if c in group_ratios.columns]
        peer_table = group_ratios[avail].copy()
        if "composite_quality_score" in peer_table.columns:
            peer_table = peer_table.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)

        rename_dict = {
            "company_id": "Ticker",
            "company_name": "Company Name",
            "composite_quality_score": "Score",
            "return_on_equity_pct": "ROE %",
            "roce_pct": "ROCE %",
            "net_profit_margin_pct": "NPM %",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF (Cr)",
            "revenue_cagr_5yr": "Rev CAGR %",
            "pat_cagr_5yr": "PAT CAGR %",
            "asset_turnover": "Asset Turn"
        }
        peer_table = peer_table.rename(columns=rename_dict)

        st.dataframe(
            peer_table.style.format({
                "Score": "{:.1f}",
                "ROE %": "{:.1f}%",
                "ROCE %": "{:.1f}%",
                "NPM %": "{:.1f}%",
                "D/E": "{:.2f}",
                "FCF (Cr)": "₹{:,.0f}",
                "Rev CAGR %": "{:.1f}%",
                "PAT CAGR %": "{:.1f}%",
                "Asset Turn": "{:.2f}"
            }, na_rep="N/A"),
            hide_index=True,
            use_container_width=True
        )

    else:
        # Head-to-Head Duel Mode
        st.markdown("""
            <div class="section-bar">
                <span class="section-bar-title">Head-to-Head Constituent Duel Matrix</span>
                <span class="section-bar-tag">Pairwise Institutional Comparison</span>
            </div>
        """, unsafe_allow_html=True)

        comps = get_companies()
        all_options = [f"{row['company_id']} - {row['company_name']}" for _, row in comps.iterrows()] if not comps.empty else []

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            comp_a_opt = st.selectbox("Select Contender A:", options=all_options, index=0 if len(all_options) > 0 else 0, key="duel_comp_a")
            ticker_a = comp_a_opt.split(" - ")[0].strip() if comp_a_opt else "TCS"
        with d_col2:
            default_b_idx = 1 if len(all_options) > 1 else 0
            comp_b_opt = st.selectbox("Select Contender B:", options=all_options, index=default_b_idx, key="duel_comp_b")
            ticker_b = comp_b_opt.split(" - ")[0].strip() if comp_b_opt else "INFY"

        r_a = all_ratios[all_ratios["company_id"] == ticker_a].iloc[-1] if not all_ratios[all_ratios["company_id"] == ticker_a].empty else {}
        r_b = all_ratios[all_ratios["company_id"] == ticker_b].iloc[-1] if not all_ratios[all_ratios["company_id"] == ticker_b].empty else {}

        val_df = get_valuation()
        val_a = val_df[val_df["company_id"] == ticker_a].iloc[0] if not val_df.empty and ticker_a in val_df["company_id"].values else {}
        val_b = val_df[val_df["company_id"] == ticker_b].iloc[0] if not val_df.empty and ticker_b in val_df["company_id"].values else {}

        duel_metrics = [
            ("Composite Quality Score", r_a.get("composite_quality_score", 0), r_b.get("composite_quality_score", 0), "{:.1f}", True),
            ("Return on Equity (ROE %)", r_a.get("return_on_equity_pct", 0), r_b.get("return_on_equity_pct", 0), "{:.1f}%", True),
            ("ROCE Efficiency %", r_a.get("roce_pct", 0), r_b.get("roce_pct", 0), "{:.1f}%", True),
            ("Net Profit Margin %", r_a.get("net_profit_margin_pct", 0), r_b.get("net_profit_margin_pct", 0), "{:.1f}%", True),
            ("Debt to Equity (D/E)", r_a.get("debt_to_equity", 0), r_b.get("debt_to_equity", 0), "{:.2f}", False),
            ("Free Cash Flow (Cr)", r_a.get("free_cash_flow_cr", 0), r_b.get("free_cash_flow_cr", 0), "₹{:,.0f}", True),
            ("5-Yr Revenue CAGR %", r_a.get("revenue_cagr_5yr", 0), r_b.get("revenue_cagr_5yr", 0), "{:.1f}%", True),
            ("P/E Multiple (x)", val_a.get("pe_ratio", 0), val_b.get("pe_ratio", 0), "{:.1f}x", False),
            ("Market Cap (INR Cr)", val_a.get("market_cap_crore", 0), val_b.get("market_cap_crore", 0), "₹{:,.0f}", True),
        ]

        score_a_wins = 0
        score_b_wins = 0

        rows = []
        for m_name, val_a_num, val_b_num, fmt, higher_better in duel_metrics:
            try:
                va = float(val_a_num) if pd.notna(val_a_num) else 0.0
                vb = float(val_b_num) if pd.notna(val_b_num) else 0.0
            except:
                va, vb = 0.0, 0.0

            if higher_better:
                winner = ticker_a if va > vb else (ticker_b if vb > va else "Tie")
            else:
                winner = ticker_a if va < vb else (ticker_b if vb < va else "Tie")

            if winner == ticker_a:
                score_a_wins += 1
            elif winner == ticker_b:
                score_b_wins += 1

            rows.append({
                "Financial Metric": m_name,
                f"{ticker_a}": fmt.format(va),
                f"{ticker_b}": fmt.format(vb),
                "Category Leader": winner
            })

        st.markdown(f"""
            <div class="bento-card" style="display: flex; justify-content: space-around; align-items: center; padding: 20px; text-align: center;">
                <div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 800; color: #00D294;">{ticker_a}</div>
                    <div style="font-size: 1.1rem; color: #F8FAFC; font-weight: 700;">{score_a_wins} Wins</div>
                </div>
                <div style="font-family: 'Libre Baskerville'; font-size: 1.4rem; color: #F59E0B; font-style: italic;">vs</div>
                <div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 800; color: #38BDF8;">{ticker_b}</div>
                    <div style="font-size: 1.1rem; color: #F8FAFC; font-weight: 700;">{score_b_wins} Wins</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
