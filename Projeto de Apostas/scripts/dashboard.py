#!/usr/bin/env python3
"""
VBQ Dashboard — Streamlit web interface for betting analytics.

Usage:
    streamlit run scripts/dashboard.py
    # or
    py -m streamlit run scripts/dashboard.py

Features:
- Real-time metrics (ROI, CLV, win rate, drawdown)
- Backtest comparison (Baseline vs Tier B)
- CLV evolution charts with league/market breakdown
- Equity curve with drawdown shading
- Configurable alert system for KPI monitoring
- Rolling metrics (30/60/90 day windows)
- Dark/light theme toggle
- Session state persistence for filters
- Export to CSV
- Daily activity heatmap
- ROI gauge vs target
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard_pages.state import init_session_state, get_state, set_state
from dashboard_pages.theme import apply_theme
from dashboard_pages.overview import render_overview
from dashboard_pages.backtests import render_backtests
from dashboard_pages.clv_analysis import render_clv_analysis
from dashboard_pages.daily_reports import render_daily_reports
from dashboard_pages.data_explorer import render_data_explorer
from dashboard_pages.system_health import render_system_health
from dashboard_pages.comparison import render_comparison
from dashboard_pages.alerts_page import render_alerts

# Page config
st.set_page_config(
    page_title="VBQ Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()


def render_sidebar() -> tuple[str, str]:
    """Render the sidebar navigation with settings and alerts."""
    with st.sidebar:
        st.title("VBQ Dashboard")
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Overview", "Backtests", "CLV Analysis", "Daily Reports",
             "Comparison", "Alerts", "Data Explorer", "System Health"],
            index=0,
            key="nav_page",
        )

        st.markdown("---")

        # Settings
        st.subheader("Settings")
        data_dir = st.text_input("Data Directory", value=get_state("data_dir", "data"), key="sidebar_data_dir")
        set_state("data_dir", data_dir)

        # Dark mode toggle
        dark_mode = st.toggle("Dark Mode", value=get_state("dark_mode", True), key="sidebar_dark_mode")
        set_state("dark_mode", dark_mode)

        st.markdown("---")

        # Quick alert summary in sidebar
        from dashboard_pages.loaders import load_clv_report, load_backtest_reports, load_daily_reports
        from dashboard_pages.alerts_engine import evaluate_alerts, alerts_summary, AlertThresholds

        clv = load_clv_report(data_dir)
        backtests = load_backtest_reports(data_dir)
        dailies = load_daily_reports(data_dir)
        thresholds = AlertThresholds(
            clv_min_pct=get_state("clv_min_threshold", 1.0),
            clv_break_even_pct=get_state("clv_break_even", 2.565),
            max_drawdown_pct=get_state("max_drawdown_pct", 20.0),
        )
        alerts = evaluate_alerts(clv, backtests, dailies, thresholds)
        summary = alerts_summary(alerts)

        # Alert badges in sidebar
        alert_text = ""
        if summary["critical"] > 0:
            alert_text += f"**{summary['critical']}** Critical  "
        if summary["warning"] > 0:
            alert_text += f"**{summary['warning']}** Warning  "
        if summary["ok"] > 0:
            alert_text += f"**{summary['ok']}** OK"

        if alert_text:
            st.markdown(f"**Alerts:** {alert_text}")

        st.markdown("---")
        st.caption("VBQ-UNIFIED v5.0.0 | Zero Cost Mode")

    return page, data_dir


def main():
    """Main dashboard entry point."""
    page, data_dir = render_sidebar()

    # Apply theme
    dark = get_state("dark_mode", True)
    apply_theme(dark=dark)

    # Route to page
    if page == "Overview":
        render_overview(data_dir, dark=dark)
    elif page == "Backtests":
        render_backtests(data_dir, dark=dark)
    elif page == "CLV Analysis":
        render_clv_analysis(data_dir, dark=dark)
    elif page == "Daily Reports":
        render_daily_reports(data_dir, dark=dark)
    elif page == "Comparison":
        render_comparison(data_dir, dark=dark)
    elif page == "Alerts":
        render_alerts(data_dir, dark=dark)
    elif page == "Data Explorer":
        render_data_explorer(data_dir, dark=dark)
    elif page == "System Health":
        render_system_health(data_dir, dark=dark)


if __name__ == "__main__":
    main()
