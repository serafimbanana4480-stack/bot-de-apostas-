"""Overview page — key metrics, alerts summary, recent backtests, ROI gauge."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from .loaders import (
    load_clv_report,
    load_train_report,
    load_backtest_reports,
    load_daily_reports,
    load_financial_viability,
)
from .alerts_engine import evaluate_alerts, alerts_summary, AlertThresholds
from .charts import roi_gauge, equity_curve_with_drawdown
from .state import get_state
from .theme import plotly_template
from .export_utils import export_csv_button


def render_overview(data_dir: str, dark: bool = True) -> None:
    """Render the overview page with key metrics, alerts, and equity curve."""
    st.header("Overview")

    # Load data
    clv = load_clv_report(data_dir)
    train = load_train_report(data_dir)
    backtests = load_backtest_reports(data_dir)
    dailies = load_daily_reports(data_dir)
    financial = load_financial_viability(data_dir)
    ptemplate = plotly_template(dark)

    # ── Alert badges row ──
    thresholds = AlertThresholds(
        clv_min_pct=get_state("clv_min_threshold", 1.0),
        clv_break_even_pct=get_state("clv_break_even", 2.565),
        max_drawdown_pct=get_state("max_drawdown_pct", 20.0),
        min_win_rate_pct=get_state("min_win_rate_pct", 45.0),
    )
    alerts = evaluate_alerts(clv, backtests, dailies, thresholds)
    summary = alerts_summary(alerts)

    # Alert banner
    badge_html = ""
    for a in alerts:
        css_class = f"alert-{a.severity.value}" if a.severity.value != "ok" else "alert-ok"
        icon = {"critical": "&#x26A0;", "warning": "&#x26A0;", "ok": "&#x2705;"}[a.severity.value]
        badge_html += f'<span class="alert-badge {css_class}">{icon} {a.name}</span>'

    if badge_html:
        st.markdown(badge_html, unsafe_allow_html=True)

    # ── KPI metrics row ──
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        mean_clv = clv.get("mean_clv_pct", 0)
        delta_clv = "Proven" if clv.get("edge_proven") else "Not Proven"
        st.metric("Mean CLV", f"{mean_clv:.2f}%", delta=delta_clv)

    with col2:
        if train.get("metrics"):
            roi = train["metrics"].get("roi", 0)
            st.metric("Training ROI", f"{(roi - 1) * 100:.1f}%")
        else:
            st.metric("Training ROI", "N/A")

    with col3:
        if backtests:
            latest = backtests[-1]
            roi_bt = latest.get("roi_per_bet", 0) * 100
            st.metric("Latest ROI", f"{roi_bt:.1f}%")
        else:
            st.metric("Latest ROI", "N/A")

    with col4:
        if backtests:
            latest = backtests[-1]
            n_bets = latest.get("total_bets", 0)
            st.metric("Backtest Bets", f"{n_bets}")
        else:
            st.metric("Backtest Bets", "N/A")

    with col5:
        if financial:
            rec = financial.get("recommendation", "N/A")
            st.metric("Viability", rec)
        else:
            st.metric("Viability", "N/A")

    st.markdown("---")

    # ── ROI Gauge + Equity Curve side by side ──
    gauge_col, equity_col = st.columns([1, 3])

    with gauge_col:
        if backtests:
            latest_roi = backtests[-1].get("roi_per_bet", 0) * 100
            fig_gauge = roi_gauge(latest_roi, target_roi=5.0, dark=dark)
            fig_gauge.update_layout(**ptemplate)
            st.plotly_chart(fig_gauge, use_container_width=True)

    with equity_col:
        # Build equity curve from daily reports
        if dailies:
            dates = [d.get("date", d.get("_filename", "?")) for d in dailies]
            bankroll = [d.get("paper_bankroll", 1000.0) for d in dailies]
            fig_eq = equity_curve_with_drawdown(
                dates, bankroll,
                title="Paper Bankroll Evolution",
                dark=dark,
                starting_bankroll=1000.0,
            )
            fig_eq.update_layout(**ptemplate)
            st.plotly_chart(fig_eq, use_container_width=True)
        elif backtests:
            # Fallback: synthetic equity from backtest cumulative PnL
            cum_pnl = 0.0
            dates_bt = []
            bankroll_bt = []
            for bt in backtests:
                cum_pnl += bt.get("total_pnl_units", 0)
                dates_bt.append(bt.get("end_date", bt.get("_filename", "?")))
                bankroll_bt.append(1000.0 + cum_pnl)
            fig_eq = equity_curve_with_drawdown(
                dates_bt, bankroll_bt,
                title="Cumulative Backtest Equity",
                dark=dark,
            )
            fig_eq.update_layout(**ptemplate)
            st.plotly_chart(fig_eq, use_container_width=True)

    st.markdown("---")

    # ── Recent Backtests table ──
    if backtests:
        st.subheader("Recent Backtests")
        bt_data = []
        for bt in backtests[-5:]:
            bt_data.append({
                "Period": f"{bt.get('start_date', '?')} -> {bt.get('end_date', '?')}",
                "Bets": bt.get("total_bets", 0),
                "ROI": f"{bt.get('roi_per_bet', 0) * 100:.1f}%",
                "Win Rate": f"{bt.get('win_rate', 0) * 100:.1f}%",
                "CLV": f"{bt.get('mean_clv_pct', 0):.1f}%",
                "Sharpe": f"{bt.get('sharpe_proxy', 0):.2f}",
                "Max DD": f"{bt.get('max_drawdown_units', 0):.1f}",
                "Leakage": bt.get("leakage_gate", "?"),
                "Reliable": "Yes" if bt.get("statistical_confidence", {}).get("reliable") else "No",
            })
        st.dataframe(pd.DataFrame(bt_data), use_container_width=True)

    # ── Training metrics ──
    if train.get("metrics") or train.get("leakage"):
        st.markdown("---")
        st.subheader("Last Training Run")
        metrics = train.get("metrics", {})
        if metrics:
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric("ROI", f"{(metrics.get('roi', 1) - 1) * 100:.1f}%")
            with m_col2:
                st.metric("Win Rate", f"{metrics.get('win_rate', 0) * 100:.1f}%")
            with m_col3:
                st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
            with m_col4:
                st.metric("Sortino", f"{metrics.get('sortino', 0):.1f}")
            with m_col5:
                st.metric("Max DD", f"{metrics.get('max_drawdown', 0) * 100:.1f}%")

        leakage = train.get("leakage", {})
        if leakage.get("passed"):
            st.success(f"Leakage Check PASSED — {len(leakage.get('suspicious_features', []))} suspicious features")
        elif leakage:
            st.error("Leakage Check FAILED")

    # ── Export ──
    if backtests:
        st.markdown("---")
        bt_export = pd.DataFrame([
            {
                "Period": f"{bt.get('start_date', '?')} -> {bt.get('end_date', '?')}",
                "Bets": bt.get("total_bets", 0),
                "ROI": bt.get("roi_per_bet", 0) * 100,
                "Win Rate": bt.get("win_rate", 0) * 100,
                "CLV": bt.get("mean_clv_pct", 0),
                "Sharpe": bt.get("sharpe_proxy", 0),
                "Max DD": bt.get("max_drawdown_units", 0),
            }
            for bt in backtests
        ])
        export_csv_button(bt_export, filename="backtests_overview.csv", label="Export Backtests CSV")
