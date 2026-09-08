"""
Annual Reports Repository View Component.
Bluestock Fintech Executive Bento Intelligence Architecture.
Zero emojis, Libre Baskerville + IBM Plex Sans + JetBrains Mono typography.
"""

import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_companies, get_documents


def render_reports_view():
    st.markdown("""
        <div class="bento-hero">
            <div class="bento-hero-tag">Regulatory Repository</div>
            <div class="bento-hero-title">Annual Reports &amp; Statutory Disclosures</div>
            <div class="bento-hero-sub">
                Official regulatory BSE corporate filings repository, auditor disclosures, and direct PDF access for Nifty 100 constituents.
            </div>
        </div>
    """, unsafe_allow_html=True)

    companies_df = get_companies()
    search_options = [f"{row['company_id']} - {row['company_name']}" for _, row in companies_df.iterrows()]

    sel_col, filter_col = st.columns([2, 1])
    with sel_col:
        selected_option = st.selectbox(
            "Select Constituent Company:",
            options=search_options,
            index=0,
            key="reports_company_select"
        )
        ticker = selected_option.split(" - ")[0].strip()

    docs_df = get_documents(ticker=ticker)

    # Sort by year descending
    if not docs_df.empty and "year" in docs_df.columns:
        docs_df = docs_df.sort_values("year", ascending=False).reset_index(drop=True)

    # Filter controls
    with filter_col:
        if not docs_df.empty:
            years_available = sorted(docs_df["year"].dropna().astype(int).unique().tolist(), reverse=True)
            year_filter = st.selectbox(
                "Filter by Year:",
                options=["All Years"] + [str(y) for y in years_available],
                index=0,
                key="reports_year_filter"
            )
            if year_filter != "All Years":
                docs_df = docs_df[docs_df["year"].astype(str) == year_filter]

    # Summary bar
    total_docs = len(docs_df) if not docs_df.empty else 0
    available_docs = docs_df["annual_report"].apply(
        lambda u: pd.notna(u) and str(u).strip().startswith("http")
    ).sum() if not docs_df.empty else 0

    st.markdown(f"""
        <div class="section-bar">
            <span class="section-bar-title">Filing Disclosures Repository: {ticker}</span>
            <span class="section-bar-tag">BSE Regulatory Feed — {available_docs}/{total_docs} Available</span>
        </div>
    """, unsafe_allow_html=True)

    if docs_df.empty:
        st.markdown("""
            <div class="bento-card" style="text-align:center; padding: 30px;">
                <div style="font-family: 'JetBrains Mono'; color: #F43F5E; font-size: 1rem; font-weight: 700;">
                    No regulatory filings registered for this company.
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        for _, doc in docs_df.iterrows():
            yr = doc.get("year", "N/A")
            url = doc.get("annual_report", "")
            is_valid_url = pd.notna(url) and str(url).strip().startswith("http")
            doc_type = doc.get("document_type", "Annual Report") if "document_type" in doc.index else "Annual Report"

            with st.container():
                col1, col2, col3 = st.columns([1.2, 0.8, 3])
                with col1:
                    st.markdown(
                        f"<span style='font-family: JetBrains Mono; font-weight: 700; color: #F8FAFC; font-size: 0.95rem;'>FY{yr}</span>",
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"<span style='font-family: IBM Plex Sans; color: #CBD5E1; font-size: 0.82rem;'>{doc_type}</span>",
                        unsafe_allow_html=True
                    )
                with col3:
                    if is_valid_url:
                        st.markdown(f"""
                            <a href="{url}" target="_blank" style="text-decoration: none;">
                                <span style="background: rgba(0, 210, 148, 0.12); color: #00D294; border: 1px solid rgba(0, 210, 148, 0.3); padding: 6px 16px; border-radius: 6px; font-weight: 700; font-size: 0.82rem; font-family: 'IBM Plex Sans';">
                                    Open BSE Statutory Filing [PDF] &nearr;
                                </span>
                            </a>
                        """, unsafe_allow_html=True)
                    else:
                        # Red "Report Unavailable" badge as specified in Sprint 4
                        st.markdown("""
                            <span style="background: rgba(244, 63, 94, 0.15); color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.3); padding: 6px 16px; border-radius: 6px; font-weight: 700; font-size: 0.82rem; font-family: 'IBM Plex Sans';">
                                Report Unavailable
                            </span>
                        """, unsafe_allow_html=True)
                st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #1F2E3D;'>", unsafe_allow_html=True)
