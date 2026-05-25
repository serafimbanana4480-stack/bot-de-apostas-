"""Alerts page — full alert dashboard with configurable thresholds."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .loaders import load_clv_report, load_backtest_reports, load_daily_reports
from .alerts_engine import evaluate_alerts, alerts_summary, AlertThresholds, Severity
from .state import get_state, set_state


def render_alerts(data_dir: str, dark: bool = True) -> None:
    """Render the alerts configuration and monitoring page."""
    st.header("Alerts & Monitoring")

    clv = load_clv_report(data_dir)
    backtests = load_backtest_reports(data_dir)
    dailies = load_daily_reports(data_dir)

    # ── Threshold Configuration ──
    st.subheader("Threshold Configuration")
    st.markdown("Adjust alert thresholds. Changes are persisted in session state.")

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        clv_min = st.number_input("Minimum CLV %", value=get_state("clv_min_threshold", 1.0),
                                    min_value=0.0, max_value=10.0, step=0.1, key="alert_clv_min")
        clv_be = st.number_input("Break-even CLV %", value=get_state("clv_break_even", 2.565),
                                   min_value=0.0, max_value=10.0, step=0.01, key="alert_clv_be")
        max_dd = st.number_input("Max Drawdown %", value=get_state("max_drawdown_pct", 20.0),
                                   min_value=5.0, max_value=50.0, step=1.0, key="alert_max_dd")
    with t_col2:
        min_wr = st.number_input("Min Win Rate %", value=get_state("min_win_rate_pct", 45.0),
                                   min_value=20.0, max_value=70.0, step=1.0, key="alert_min_wr")
        min_pf = st.number_input("Min Profit Factor", value=1.1,
                                   min_value=0.5, max_value=3.0, step=0.1, key="alert_min_pf")
        min_bets = st.number_input("Min Bets for Confidence", value=50,
                                    min_value=10, max_value=500, step=10, key="alert_min_bets")

    # Persist to session state
    set_state("clv_min_threshold", clv_min)
    set_state("clv_break_even", clv_be)
    set_state("max_drawdown_pct", max_dd)
    set_state("min_win_rate_pct", min_wr)

    thresholds = AlertThresholds(
        clv_min_pct=clv_min,
        clv_break_even_pct=clv_be,
        max_drawdown_pct=max_dd,
        min_win_rate_pct=min_wr,
        min_profit_factor=min_pf,
        min_bets_for_confidence=min_bets,
    )

    # ── Evaluate Alerts ──
    st.markdown("---")
    st.subheader("Current Alert Status")

    alerts = evaluate_alerts(clv, backtests, dailies, thresholds)
    summary = alerts_summary(alerts)

    # Summary badges
    badge_html = ""
    if summary["critical"] > 0:
        badge_html += f'<span class="alert-badge alert-critical">CRITICAL: {summary["critical"]}</span>'
    if summary["warning"] > 0:
        badge_html += f'<span class="alert-badge alert-warning">WARNING: {summary["warning"]}</span>'
    if summary["ok"] > 0:
        badge_html += f'<span class="alert-badge alert-ok">OK: {summary["ok"]}</span>'
    st.markdown(badge_html, unsafe_allow_html=True)

    # ── Alert Details Table ──
    alert_rows = []
    for a in alerts:
        severity_icon = {"critical": "CRITICAL", "warning": "WARNING", "ok": "OK"}[a.severity.value]
        alert_rows.append({
            "Severity": severity_icon,
            "Alert": a.name,
            "Current Value": f"{a.value:.2f}",
            "Threshold": f"{a.threshold:.2f}",
            "Message": a.message,
        })

    if alert_rows:
        df_alerts = pd.DataFrame(alert_rows)
        # Color-code by severity
        def _severity_color(val):
            if val == "CRITICAL":
                return "background-color: #3d1118; color: #f85149" if dark else "background-color: #ffe0e0; color: #c00"
            elif val == "WARNING":
                return "background-color: #3d2e00; color: #d29922" if dark else "background-color: #fff3cd; color: #856404"
            return "background-color: #0d2818; color: #3fb950" if dark else "background-color: #d4edda; color: #155724"

        styled = df_alerts.style.applymap(_severity_color, subset=["Severity"])
        st.dataframe(styled, use_container_width=True, height=300)

    # ── Live Readiness Check ──
    st.markdown("---")
    st.subheader("Live Trading Readiness")

    critical_count = summary["critical"]
    warning_count = summary["warning"]

    if critical_count > 0:
        st.error(f"NOT READY — {critical_count} critical alert(s) must be resolved before going live")
        st.markdown("**Action required:** Resolve all CRITICAL alerts before enabling live execution")
    elif warning_count > 0:
        st.warning(f"CAUTION — {warning_count} warning(s) detected. Live trading possible but monitor closely")
        st.markdown("**Recommendation:** Monitor these warnings and set up automated checks")
    else:
        st.success("READY — All KPIs within acceptable thresholds")
        st.markdown("**Status:** System passes all alert checks. CLV validated, drawdown controlled, edge proven.")

    # ── Alert History Placeholder ──
    st.markdown("---")
    st.subheader("Alert Log")
    st.info("Alert history will be tracked when daily pipeline runs are automated. "
            "Run `py scripts/daily_report.py` to generate daily snapshots.")
