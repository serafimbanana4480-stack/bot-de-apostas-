"""Theme management — dark/light mode CSS and visual identity."""
from __future__ import annotations

import streamlit as st

# Professional dark theme for betting analytics
DARK_CSS = """
<style>
    /* ── Base overrides ── */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #c9d1d9;
    }
    section[data-testid="stSidebar"] .stRadio > label[data-checked="true"] {
        color: #58a6ff;
        background-color: #1f2937;
        border-color: #58a6ff;
    }

    /* ── Metric cards ── */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    [data-testid="stMetricDeltaNegative"] {
        color: #f85149;
    }
    [data-testid="stMetricDeltaPositive"] {
        color: #3fb950;
    }

    /* ── DataFrames ── */
    .stDataFrame {
        background-color: #161b22;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #161b22;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 600;
        color: #8b949e;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #58a6ff;
        background-color: #1f2937;
    }

    /* ── Alert badges ── */
    .alert-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin: 2px 4px;
    }
    .alert-critical {
        background-color: #3d1118;
        color: #f85149;
        border: 1px solid #f8514944;
    }
    .alert-warning {
        background-color: #3d2e00;
        color: #d29922;
        border: 1px solid #d2992244;
    }
    .alert-ok {
        background-color: #0d2818;
        color: #3fb950;
        border: 1px solid #3fb95044;
    }

    /* ── Custom metric card ── */
    .vbq-metric-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        text-align: center;
    }
    .vbq-metric-card .label {
        font-size: 12px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .vbq-metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        margin: 4px 0;
    }
    .vbq-metric-card .delta {
        font-size: 0.85rem;
    }
    .vbq-metric-card .value.positive { color: #3fb950; }
    .vbq-metric-card .value.negative { color: #f85149; }
    .vbq-metric-card .value.neutral  { color: #58a6ff; }

    /* ── Section headers ── */
    .vbq-section {
        border-left: 3px solid #58a6ff;
        padding-left: 12px;
        margin: 16px 0;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #30363d;
        background-color: #21262d;
        color: #c9d1d9;
    }
    .stButton > button:hover {
        border-color: #58a6ff;
        background-color: #1f2937;
    }

    /* ── Plotly chart container ── */
    .stPlotlyChart {
        background-color: #161b22;
        border-radius: 12px;
        border: 1px solid #30363d;
        padding: 8px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
</style>
"""

LIGHT_CSS = """
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .success { color: #00cc00; }
    .warning { color: #ff9900; }
    .danger { color: #ff3333; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 500; }
</style>
"""

PLOTLY_DARK_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#c9d1d9", "family": "Inter, system-ui, sans-serif"},
    "xaxis": {"gridcolor": "#21262d", "zerolinecolor": "#30363d"},
    "yaxis": {"gridcolor": "#21262d", "zerolinecolor": "#30363d"},
    "title_font": {"size": 16, "color": "#e0e0e0"},
    "legend": {"bgcolor": "rgba(22,27,34,0.8)", "bordercolor": "#30363d", "borderwidth": 1},
    "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
}

PLOTLY_LIGHT_LAYOUT = {
    "paper_bgcolor": "rgba(255,255,255,0)",
    "plot_bgcolor": "rgba(255,255,255,0)",
    "font": {"color": "#333", "family": "Inter, system-ui, sans-serif"},
    "xaxis": {"gridcolor": "#e0e0e0", "zerolinecolor": "#ccc"},
    "yaxis": {"gridcolor": "#e0e0e0", "zerolinecolor": "#ccc"},
    "title_font": {"size": 16, "color": "#333"},
    "legend": {"bgcolor": "rgba(255,255,255,0.8)", "bordercolor": "#ddd", "borderwidth": 1},
    "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
}


def apply_theme(dark: bool = True) -> dict:
    """Apply CSS theme and return Plotly layout template for charts."""
    css = DARK_CSS if dark else LIGHT_CSS
    st.markdown(css, unsafe_allow_html=True)
    return PLOTLY_DARK_LAYOUT if dark else PLOTLY_LIGHT_LAYOUT


def plotly_template(dark: bool = True) -> dict:
    """Return Plotly layout defaults matching the current theme."""
    return PLOTLY_DARK_LAYOUT if dark else PLOTLY_LIGHT_LAYOUT
