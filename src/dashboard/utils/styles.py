"""
Bluestock Fintech Executive Bento Intelligence Design System.
Theme: Obsidian Dark Slate Canvas (#080E11) + Mint Emerald Jade (#00D294) + Sovereign Gold (#F59E0B).
Typography: Title: Libre Baskerville | Body: IBM Plex Sans | Metrics: JetBrains Mono.
Zero emojis, 100% WCAG AAA Color-Blind Safe, Bento Grid High-Density Architecture.
"""

import streamlit as st

# Executive Dark Bento Palette
PALETTE = {
    "canvas": "#080E11",         # Deep Obsidian Canvas
    "canvas_alt": "#0D141C",     # Deep Slate Background
    "surface": "#111A22",        # Primary Bento Card Surface
    "surface_elevated": "#18232F", # Hover / Elevated Card Surface
    "border": "#1F2E3D",         # Subtle Card Border
    "border_highlight": "#00D294", # Emerald Active Border
    "primary": "#00D294",        # Mint Emerald Jade / Capital Alpha
    "primary_glow": "rgba(0, 210, 148, 0.15)",
    "secondary": "#F59E0B",      # Sovereign Champagne Gold / Benchmark
    "secondary_glow": "rgba(245, 158, 11, 0.15)",
    "accent_teal": "#0D9488",    # Deep Teal
    "accent_violet": "#8B5CF6",  # Modern Violet
    "danger": "#F43F5E",         # Accessible Rose Coral
    "danger_glow": "rgba(244, 63, 94, 0.15)",
    "text_primary": "#F8FAFC",   # High Contrast White / Slate 50
    "text_secondary": "#94A3B8", # Slate 400 Muted Text
    "text_dark": "#080E11",      # Dark text for light badges
    "chart_series": [
        "#00D294",  # Mint Emerald
        "#F59E0B",  # Sovereign Gold
        "#38BDF8",  # Sky Cyan
        "#A855F7",  # Violet
        "#F43F5E",  # Rose Coral
        "#2DD4BF",  # Aqua Teal
        "#FB923C",  # Tangerine
        "#94A3B8",  # Slate
    ]
}


def apply_executive_css():
    """Inject custom Obsidian Bento Intelligence styling with Libre Baskerville & IBM Plex Sans."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
        
        /* Global Base */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #F8FAFC;
        }

        /* App Background */
        .stApp {
            background-color: #080E11 !important;
            color: #F8FAFC !important;
        }

        /* Titles and Editorial Headers */
        h1, h2, h3, .baskerville-title {
            font-family: 'Libre Baskerville', Georgia, serif !important;
            font-weight: 700 !important;
            color: #F8FAFC !important;
            letter-spacing: -0.01em;
        }

        /* Bento Hero Banner */
        .bento-hero {
            background: linear-gradient(135deg, #0D1620 0%, #111A22 60%, #152230 100%);
            border: 1px solid #1F2E3D;
            border-left: 5px solid #00D294;
            border-radius: 12px;
            padding: 24px 30px;
            margin-bottom: 24px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 210, 148, 0.05);
            position: relative;
            overflow: hidden;
        }
        .bento-hero::after {
            content: "";
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(0, 210, 148, 0.08) 0%, transparent 70%);
            pointer-events: none;
        }
        .bento-hero-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 700;
            color: #00D294;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 8px;
            display: inline-block;
            background: rgba(0, 210, 148, 0.10);
            padding: 3px 10px;
            border-radius: 4px;
            border: 1px solid rgba(0, 210, 148, 0.25);
        }
        .bento-hero-title {
            font-family: 'Libre Baskerville', Georgia, serif;
            font-size: 1.85rem;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.25;
            margin-bottom: 8px;
        }
        .bento-hero-sub {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.94rem;
            color: #CBD5E1;
            line-height: 1.6;
            max-width: 900px;
        }

        /* Bento Grid Card */
        .bento-card {
            background: #111A22;
            border: 1px solid #1F2E3D;
            border-radius: 12px;
            padding: 20px 22px;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: all 0.25s ease-in-out;
            position: relative;
        }
        .bento-card:hover {
            border-color: #00D294;
            box-shadow: 0 8px 30px rgba(0, 210, 148, 0.12);
            transform: translateY(-2px);
        }
        .bento-card-gold:hover {
            border-color: #F59E0B;
            box-shadow: 0 8px 30px rgba(245, 158, 11, 0.12);
        }

        /* Bento KPI Stat Tiles */
        .bento-stat-label {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.74rem;
            font-weight: 600;
            color: #CBD5E1;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .bento-stat-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.2;
        }
        .bento-stat-sub {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.78rem;
            color: #94A3B8;
            margin-top: 6px;
        }

        /* Bento Badges & Status Pills */
        .bento-badge-emerald {
            display: inline-block;
            background: rgba(0, 210, 148, 0.15);
            color: #00D294;
            border: 1px solid rgba(0, 210, 148, 0.35);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .bento-badge-gold {
            display: inline-block;
            background: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            border: 1px solid rgba(245, 158, 11, 0.35);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .bento-badge-coral {
            display: inline-block;
            background: rgba(244, 63, 94, 0.15);
            color: #F43F5E;
            border: 1px solid rgba(244, 63, 94, 0.35);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .bento-badge-slate {
            display: inline-block;
            background: rgba(148, 163, 184, 0.18);
            color: #E2E8F0;
            border: 1px solid rgba(148, 163, 184, 0.4);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }

        /* Section Bar Divider */
        .section-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #1F2E3D;
            padding-bottom: 10px;
            margin-top: 28px;
            margin-bottom: 18px;
        }
        .section-bar-title {
            font-family: 'Libre Baskerville', Georgia, serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: -0.01em;
        }
        .section-bar-tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: #00D294;
            background: rgba(0, 210, 148, 0.08);
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid rgba(0, 210, 148, 0.2);
        }

        /* Investment Thesis Cards */
        .box-strength {
            background: rgba(0, 210, 148, 0.06);
            border-left: 4px solid #00D294;
            border-top: 1px solid rgba(0, 210, 148, 0.15);
            border-right: 1px solid rgba(0, 210, 148, 0.15);
            border-bottom: 1px solid rgba(0, 210, 148, 0.15);
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 10px;
            color: #E2E8F0;
            font-size: 0.88rem;
            line-height: 1.5;
        }
        .box-risk {
            background: rgba(244, 63, 94, 0.06);
            border-left: 4px solid #F43F5E;
            border-top: 1px solid rgba(244, 63, 94, 0.15);
            border-right: 1px solid rgba(244, 63, 94, 0.15);
            border-bottom: 1px solid rgba(244, 63, 94, 0.15);
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 10px;
            color: #E2E8F0;
            font-size: 0.88rem;
            line-height: 1.5;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0D141C !important;
            border-right: 1px solid #1F2E3D !important;
        }
        section[data-testid="stSidebar"] .stRadio label {
            color: #94A3B8 !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            transition: all 0.2s ease !important;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            background-color: rgba(0, 210, 148, 0.08) !important;
            color: #00D294 !important;
        }

        /* Dataframe Dark Theme */
        .stDataFrame, div[data-testid="stTable"] {
            background-color: #111A22 !important;
            border-radius: 8px !important;
            border: 1px solid #1F2E3D !important;
        }

        /* Live Market Ticker Ribbon */
        .ticker-ribbon {
            background: #0D1620;
            border: 1px solid #1F2E3D;
            border-radius: 8px;
            padding: 8px 16px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            overflow-x: auto;
            white-space: nowrap;
            gap: 18px;
            box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
        }
        .ticker-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
        }
        .ticker-symbol {
            color: #FFFFFF;
            font-weight: 700;
        }
        .ticker-val {
            color: #94A3B8;
        }
        .ticker-pos {
            color: #00D294;
            font-weight: 700;
        }
        .ticker-neg {
            color: #F43F5E;
            font-weight: 700;
        }

        /* Live Pulsing Dot */
        .live-pulse {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #00D294;
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 10px #00D294;
            animation: pulse-animation 2s infinite;
        }
        @keyframes pulse-animation {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 210, 148, 0.7); }
            70% { transform: scale(1.15); box-shadow: 0 0 0 8px rgba(0, 210, 148, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 210, 148, 0); }
        }

        /* Clean Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def get_plotly_bento_layout(title: str = "", height: int = 400) -> dict:
    """Return crisp dark Bento Intelligence layout for Plotly figures."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Libre Baskerville, Georgia, serif", size=13, color="#F8FAFC"),
            x=0.01,
            y=0.96
        ),
        paper_bgcolor="#111A22",
        plot_bgcolor="#0C131D",
        font=dict(family="IBM Plex Sans, sans-serif", size=11, color="#E2E8F0"),
        margin=dict(l=45, r=30, t=45, b=40),
        height=height,
        hoverlabel=dict(
            bgcolor="#080E11",
            font=dict(family="JetBrains Mono, monospace", size=11, color="#FFFFFF"),
            bordercolor="#00D294"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1F2E3D",
            linecolor="#1F2E3D",
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#CBD5E1")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1F2E3D",
            linecolor="#1F2E3D",
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#CBD5E1")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(family="IBM Plex Sans, sans-serif", size=11, color="#F8FAFC")
        )
    )


def create_financial_health_gauge(score: float, title: str = "Fundamental Health Score") -> dict:
    """Return Plotly Gauge Indicator figure dictionary."""
    import plotly.graph_objects as go
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>{title}</b>", 'font': {'size': 13, 'family': 'Libre Baskerville, serif', 'color': '#F8FAFC'}},
        number={'suffix': "/100", 'font': {'size': 24, 'family': 'JetBrains Mono, monospace', 'color': '#FFFFFF'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': "#00D294", 'thickness': 0.28},
            'bgcolor': "#0C131D",
            'borderwidth': 1,
            'bordercolor': "#1F2E3D",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(244, 63, 94, 0.25)'},
                {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.25)'},
                {'range': [70, 100], 'color': 'rgba(0, 210, 148, 0.25)'}
            ],
            'threshold': {
                'line': {'color': "#F59E0B", 'width': 3},
                'thickness': 0.8,
                'value': score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="#111A22",
        plot_bgcolor="#111A22",
        height=220,
        margin=dict(l=25, r=25, t=35, b=20)
    )
    return fig


# Backward compatibility aliases
apply_institutional_css = apply_executive_css
get_plotly_exec_layout = get_plotly_bento_layout
get_plotly_fin_layout = get_plotly_bento_layout
