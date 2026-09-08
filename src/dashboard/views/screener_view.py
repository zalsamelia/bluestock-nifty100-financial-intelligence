"""
Financial Screener View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import streamlit as st

from src.screener.engine import (
    load_screener_config,
    load_full_screener_dataset,
    apply_threshold_filters,
    calculate_composite_quality_score,
)


def render_screener_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Screener & Quant Engine</div>
            <div class="bento-hero-title">Quantitative Multi-Factor Financial Screener</div>
            <div class="bento-hero-sub">
                Apply institutional quality, value, growth, leverage, and cash flow filters across the Nifty 100 universe. Dynamically recalculate composite quality scores with instant CSV exports.
            </div>
        </div>
    """, unsafe_allow_html=True)

    config = load_screener_config()
    full_df = load_full_screener_dataset(target_year=2024)

    # Preset Templates
    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Institutional Preset Archetypes</span>
            <span class="section-bar-tag">6 Quant Screening Presets</span>
        </div>
    """, unsafe_allow_html=True)
    
    presets = [
        ("Quality Compounder", "quality_compounder"),
        ("Value Pick", "value_pick"),
        ("Growth Accelerator", "growth_accelerator"),
        ("Dividend Champion", "dividend_champion"),
        ("Debt-Free Blue Chip", "debt_free_blue_chip"),
        ("Turnaround Watch", "turnaround_watch"),
    ]

    if "scr_sliders" not in st.session_state:
        st.session_state["scr_sliders"] = {
            "roe_min": 0.0, "de_max": 5.0, "fcf_min": -500.0, "rev_cagr_min": 0.0,
            "pat_cagr_min": 0.0, "opm_min": 0.0, "pe_max": 100.0, "pb_max": 20.0,
            "div_yield_min": 0.0, "icr_min": 0.0,
        }

    b_cols = st.columns(6)
    for idx, (label, p_key) in enumerate(presets):
        if b_cols[idx].button(label, use_container_width=True, key=f"btn_p_{p_key}"):
            p_filters = config["presets"][p_key]["filters"]
            st.session_state["scr_sliders"]["roe_min"] = float(p_filters.get("return_on_equity_pct_min", 0.0))
            st.session_state["scr_sliders"]["de_max"] = float(p_filters.get("debt_to_equity_max", 5.0))
            st.session_state["scr_sliders"]["fcf_min"] = float(p_filters.get("free_cash_flow_cr_min", -500.0))
            st.session_state["scr_sliders"]["rev_cagr_min"] = float(p_filters.get("revenue_cagr_5yr_min", p_filters.get("revenue_cagr_3yr_min", 0.0)))
            st.session_state["scr_sliders"]["pat_cagr_min"] = float(p_filters.get("pat_cagr_5yr_min", 0.0))
            st.session_state["scr_sliders"]["opm_min"] = float(p_filters.get("operating_profit_margin_pct_min", 0.0))
            st.session_state["scr_sliders"]["pe_max"] = float(p_filters.get("pe_ratio_max", 100.0))
            st.session_state["scr_sliders"]["pb_max"] = float(p_filters.get("pb_ratio_max", 20.0))
            st.session_state["scr_sliders"]["div_yield_min"] = float(p_filters.get("dividend_yield_pct_min", 0.0))
            st.session_state["scr_sliders"]["icr_min"] = float(p_filters.get("interest_coverage_min", 0.0))
            st.rerun()

    st.markdown("""
        <div class="section-bar">
            <span class="section-bar-title">Multi-Metric Quantitative Thresholds</span>
            <span class="section-bar-tag">10 Interactive Filter Sliders</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 2 rows of 5 sliders
    sl_col1, sl_col2, sl_col3, sl_col4, sl_col5 = st.columns(5)
    with sl_col1:
        roe_s = st.slider("Min ROE %", 0.0, 50.0, st.session_state["scr_sliders"]["roe_min"], step=1.0)
    with sl_col2:
        de_s = st.slider("Max D/E", 0.0, 5.0, st.session_state["scr_sliders"]["de_max"], step=0.1)
    with sl_col3:
        fcf_s = st.slider("Min FCF (Cr)", -500.0, 5000.0, st.session_state["scr_sliders"]["fcf_min"], step=100.0)
    with sl_col4:
        rev_s = st.slider("Min Rev CAGR %", 0.0, 30.0, st.session_state["scr_sliders"]["rev_cagr_min"], step=1.0)
    with sl_col5:
        pat_s = st.slider("Min PAT CAGR %", 0.0, 30.0, st.session_state["scr_sliders"]["pat_cagr_min"], step=1.0)

    sl2_1, sl2_2, sl2_3, sl2_4, sl2_5 = st.columns(5)
    with sl2_1:
        opm_s = st.slider("Min OPM %", 0.0, 50.0, st.session_state["scr_sliders"]["opm_min"], step=1.0)
    with sl2_2:
        pe_s = st.slider("Max P/E", 5.0, 100.0, st.session_state["scr_sliders"]["pe_max"], step=1.0)
    with sl2_3:
        pb_s = st.slider("Max P/B", 0.5, 20.0, st.session_state["scr_sliders"]["pb_max"], step=0.5)
    with sl2_4:
        div_s = st.slider("Min Div Yield %", 0.0, 10.0, st.session_state["scr_sliders"]["div_yield_min"], step=0.5)
    with sl2_5:
        icr_s = st.slider("Min ICR", 0.0, 20.0, st.session_state["scr_sliders"]["icr_min"], step=1.0)

    # Filter data
    active_filters = {
        "return_on_equity_pct_min": roe_s if roe_s > 0 else None,
        "debt_to_equity_max": de_s if de_s < 5.0 else None,
        "free_cash_flow_cr_min": fcf_s if fcf_s > -500 else None,
        "revenue_cagr_5yr_min": rev_s if rev_s > 0 else None,
        "pat_cagr_5yr_min": pat_s if pat_s > 0 else None,
        "operating_profit_margin_pct_min": opm_s if opm_s > 0 else None,
        "pe_ratio_max": pe_s if pe_s < 100.0 else None,
        "pb_ratio_max": pb_s if pb_s < 20.0 else None,
        "dividend_yield_pct_min": div_s if div_s > 0 else None,
        "interest_coverage_min": icr_s if icr_s > 0 else None,
    }

    filtered = apply_threshold_filters(full_df, active_filters, is_financials_carveout=True)
    scored = calculate_composite_quality_score(filtered)
    sorted_res = scored.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)

    # Summary and Export header
    head_left, head_right = st.columns([3, 1])
    with head_left:
        st.markdown(f"""
            <div class="bento-card" style="padding: 14px 20px; margin-top: 15px; margin-bottom: 14px;">
                <span style="font-weight: 800; color: #00D294; font-size: 1.25rem; font-family: 'JetBrains Mono';">{len(sorted_res)} Constituents Matched</span>
                <span style="color: #94A3B8; font-size: 0.90rem; font-family: 'IBM Plex Sans';"> out of 92 active Nifty 100 coverage universe.</span>
            </div>
        """, unsafe_allow_html=True)

    # Prepare table columns
    disp_cols = [
        "company_id", "company_name", "sector", "composite_quality_score",
        "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct",
        "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage"
    ]
    avail = [c for c in disp_cols if c in sorted_res.columns]
    out_table = sorted_res[avail].copy()
    
    col_rename = {
        "company_id": "Ticker",
        "company_name": "Company Name",
        "sector": "Sector",
        "composite_quality_score": "Score",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Rev CAGR %",
        "pat_cagr_5yr": "PAT CAGR %",
        "operating_profit_margin_pct": "OPM %",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Div Yield %",
        "interest_coverage": "ICR"
    }
    out_table = out_table.rename(columns=col_rename)

    with head_right:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        csv_data = out_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Filtered CSV",
            data=csv_data,
            file_name="bluestock_screener_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.dataframe(
        out_table.style.format({
            "Score": "{:.1f}",
            "ROE %": "{:.1f}%",
            "D/E": "{:.2f}",
            "FCF (Cr)": "₹{:,.0f}",
            "Rev CAGR %": "{:.1f}%",
            "PAT CAGR %": "{:.1f}%",
            "OPM %": "{:.1f}%",
            "P/E": "{:.1f}x",
            "P/B": "{:.1f}x",
            "Div Yield %": "{:.1f}%",
            "ICR": "{:.1f}x"
        }, na_rep="N/A"),
        hide_index=True,
        use_container_width=True,
        height=480
    )
