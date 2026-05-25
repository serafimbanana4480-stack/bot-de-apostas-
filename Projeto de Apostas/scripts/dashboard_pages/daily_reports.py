"""Daily Reports page — timeline, bankroll evolution, rolling metrics, activity heatmap."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from .loaders import load_daily_reports
from .charts import equity_curve_with_drawdown, daily_activity_heatmap
from .state import get_state
from .theme import plotly_template


def render_daily_reports(data_dir: str, dark: bool = True) -> None:
    """Render daily report timeline with rolling metrics and activity heatmap."""
    st.header("Daily Reports")

    dailies = load_daily_reports(data_dir)
    ptemplate = plotly_template(dark)

    if not dailies:
        st.info("No daily reports found. Run: `py scripts/daily_report.py`")
        return

    # Build DataFrame
    df = pd.DataFrame([
        {
            "Date": d.get("date", d.get("_filename", "?")),
            "Bets": d.get("bets_placed", 0),
            "Opportunities": d.get("opportunities", 0),
            "Paper Bankroll": d.get("paper_bankroll", 1000),
            "Tier B Sharp": d.get("tier_b", {}).get("sharp", False),
            "Tier B Dynamic EV": d.get("tier_b", {}).get("dynamic_ev", False),
        }
        for d in dailies
    ])

    # ── Timeline table ──
    st.subheader("Daily Activity Timeline")
    st.dataframe(df, use_container_width=True)

    # ── Activity vs Bets chart ──
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Opportunities"], mode="lines+markers",
        name="Opportunities",
        line=dict(color="#58a6ff" if dark else "#1f77b4"),
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Bets"], mode="lines+markers",
        name="Bets Placed",
        line=dict(color="#3fb950" if dark else "#2ca02c"),
    ))
    fig.update_layout(title="Daily Opportunities vs Bets", xaxis_title="Date", yaxis_title="Count", **ptemplate)
    st.plotly_chart(fig, use_container_width=True)

    # ── Bankroll evolution with drawdown (ENHANCED) ──
    st.subheader("Bankroll Evolution & Drawdown")
    fig_eq = equity_curve_with_drawdown(
        df["Date"].tolist(), df["Paper Bankroll"].tolist(),
        title="Paper Bankroll with Drawdown",
        dark=dark,
        starting_bankroll=1000.0,
    )
    fig_eq.update_layout(**ptemplate)
    st.plotly_chart(fig_eq, use_container_width=True)

    # ── Rolling Metrics (NEW) ──
    st.subheader("Rolling Metrics")
    window = st.slider("Rolling Window (days)", 7, 90,
                        value=get_state("rolling_window_days", 30),
                        key="rolling_window_daily")

    if len(df) >= 2:
        # Compute rolling ROI, win rate proxy
        df["Daily PnL"] = df["Paper Bankroll"].diff().fillna(0)
        df["Cumulative PnL"] = df["Daily PnL"].cumsum()
        df["Rolling PnL"] = df["Daily PnL"].rolling(window=min(window, len(df)), min_periods=1).sum()
        df["Rolling Bankroll Avg"] = df["Paper Bankroll"].rolling(window=min(window, len(df)), min_periods=1).mean()

        fig_roll = make_subplots_with_rolling(df, window, dark)
        fig_roll.update_layout(**ptemplate)
        st.plotly_chart(fig_roll, use_container_width=True)
    else:
        st.info("Need more daily data points for rolling metrics")

    # ── Daily Activity Heatmap (NEW) ──
    st.subheader("Activity Heatmap")
    if len(df) >= 7:
        fig_heat = daily_activity_heatmap(
            df["Date"].tolist(), df["Bets"].tolist(), dark=dark,
        )
        fig_heat.update_layout(**ptemplate)
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Monte Carlo from latest daily (if available) ──
    latest_daily = dailies[-1] if dailies else {}
    mc = latest_daily.get("monte_carlo", {})
    if mc:
        st.subheader("Monte Carlo Simulation (Latest)")
        mc_col1, mc_col2, mc_col3, mc_col4 = st.columns(4)
        with mc_col1:
            st.metric("Mean Final Bankroll", f"{mc.get('mean_final_bankroll', 0):.0f}")
        with mc_col2:
            st.metric("Profit Probability", f"{mc.get('profit_probability', 0) * 100:.1f}%")
        with mc_col3:
            st.metric("Ruin Probability", f"{mc.get('ruin_probability', 0) * 100:.1f}%")
        with mc_col4:
            st.metric("Mean Max DD %", f"{mc.get('mean_max_drawdown_pct', 0):.1f}%")


def make_subplots_with_rolling(df: pd.DataFrame, window: int, dark: bool = True) -> go.Figure:
    """Build rolling metrics subplot chart."""
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
        subplot_titles=("Rolling PnL", "Bankroll"),
    )

    pnl_color = "#3fb950" if dark else "#2ca02c"
    bankroll_color = "#58a6ff" if dark else "#1f77b4"

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Rolling PnL"], mode="lines",
        name=f"Rolling {window}d PnL",
        line=dict(color=pnl_color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba(63,185,80,0.1)" if dark else "rgba(44,160,44,0.1)",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Paper Bankroll"], mode="lines",
        name="Bankroll",
        line=dict(color=bankroll_color, width=2),
    ), row=2, col=1)

    fig.add_hline(y=0, line_color="#30363d" if dark else "#ccc", row=1, col=1)
    fig.add_hline(y=1000, line_dash="dash",
                   line_color="#f85149" if dark else "#d62728", row=2, col=1)

    return fig
