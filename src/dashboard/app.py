"""
Main Streamlit Application Entry Point (Sprint 4).
Institutional-grade dark financial terminal aesthetic.
Features interactive sidebar navigation across all 8 core analytics modules.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.styles import apply_institutional_css
from src.dashboard.views.home_view import render_home_view
from src.dashboard.views.profile_view import render_profile_view
from src.dashboard.views.screener_view import render_screener_view
from src.dashboard.views.peers_view import render_peers_view
from src.dashboard.views.trends_view import render_trends_view
from src.dashboard.views.sectors_view import render_sectors_view
from src.dashboard.views.capital_view import render_capital_view
from src.dashboard.views.reports_view import render_reports_view

# 1. Page Configuration
st.set_page_config(
    page_title="Nifty 100 Financial Intelligence",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_institutional_css()

# 2. Sidebar Navigation
with st.sidebar:
    st.markdown("""
        <div style="padding: 12px 4px 18px 4px;">
            <div style="font-family: 'Libre Baskerville', Georgia, serif; font-size: 1.25rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.01em;">BLUESTOCK</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; font-weight: 700; color: #00D294; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 2px;">Fintech Intelligence Hub</div>
            <div style="display: flex; gap: 6px; margin-top: 10px;">
                <span style="background: rgba(0, 210, 148, 0.12); color: #00D294; border: 1px solid rgba(0, 210, 148, 0.25); font-size: 0.65rem; font-family: 'JetBrains Mono'; padding: 2px 6px; border-radius: 4px; font-weight: 700;">LIVE FEED</span>
                <span style="background: rgba(245, 158, 11, 0.12); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.25); font-size: 0.65rem; font-family: 'JetBrains Mono'; padding: 2px 6px; border-radius: 4px; font-weight: 700;">NIFTY 100</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='border-top: 1px solid #1F2E3D; margin-bottom: 14px;'></div>", unsafe_allow_html=True)
    
    NAV_OPTIONS = [
        "01. Market Overview",
        "02. Company Profile",
        "03. Financial Screener",
        "04. Peer Benchmark",
        "05. Historical Trends",
        "06. Sector Dynamics",
        "07. Capital Allocation",
        "08. Annual Reports"
    ]

    selected_screen = st.radio(
        "NAVIGATION",
        options=NAV_OPTIONS,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<div style='border-top: 1px solid #1F2E3D; margin-top: 28px; margin-bottom: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family: 'IBM Plex Sans'; font-size: 0.72rem; color: #64748B; line-height: 1.4;">
            <div style="color: #94A3B8; font-weight: 600; margin-bottom: 4px;">Institutional Research Terminal</div>
            <div>Constituents: 92 Companies</div>
            <div>Data Horizon: FY2011–FY2024</div>
            <div style="margin-top: 6px; color: #00D294; font-family: 'JetBrains Mono'; font-weight: 600;">Bluestock Analytics Engine v4.2</div>
        </div>
    """, unsafe_allow_html=True)

# 3. Main Screen View Dispatcher
if selected_screen == "01. Market Overview":
    render_home_view()
elif selected_screen == "02. Company Profile":
    render_profile_view()
elif selected_screen == "03. Financial Screener":
    render_screener_view()
elif selected_screen == "04. Peer Benchmark":
    render_peers_view()
elif selected_screen == "05. Historical Trends":
    render_trends_view()
elif selected_screen == "06. Sector Dynamics":
    render_sectors_view()
elif selected_screen == "07. Capital Allocation":
    render_capital_view()
elif selected_screen == "08. Annual Reports":
    render_reports_view()
