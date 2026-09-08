import sys
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.styles import apply_institutional_css
from src.dashboard.views.profile_view import render_profile_view

st.set_page_config(page_title="Company Profile | Nifty 100", layout="wide")
apply_institutional_css()
render_profile_view()
