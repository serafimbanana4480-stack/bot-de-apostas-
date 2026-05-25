"""Comparison page — Baseline vs Tier B side-by-side equity and metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .loaders import load_backtest_reports, load_paper_comparison, load_daily_reports
from .charts import baseline_vs_tier_b_comparison
from .theme import plotly_template


def render_comparison(data_dir: str, dark: bool = True) -> None:
    """Render Baseline vs Tier B comparison page."""
    st.header("Baseline vs Tier B Comparison")

    backtests = load_backtest_reports(data_dir)
    paper_comp = load_paper_comparison(data_dir)
    dailies = load_daily_reports(data_dir)
    ptemplate = plotly_template(dark)

    # ── Backtest vs Paper Trading Comparison ──
    if paper_comp:
        st.subheader("Backtest vs Paper Trading")
        bt_data = paper_comp.get("backtest", {})
        paper_data = paper_comp.get("paper", {})

        # Metrics comparison table
        comp_df = pd.DataFrame({
            "Metric": ["Total Bets", "ROI per Bet", "Win Rate", "Profit Factor",
                        "Sharpe", "Max Drawdown (units)", "Mean CLV %", "Total PnL (units)"],
            "Backtest": [
                bt_data.get("total_bets", 0),
                f"{bt_data.get('roi_per_bet', 0) * 100:.2f}%",
                f"{bt_data.get('win_rate', 0) * 100:.1f}%",
                f"{bt_data.get('profit_factor', 0):.2f}",
                f"{bt_data.get('sharpe_proxy', 0):.2f}",
                f"{bt_data.get('max_drawdown_units', 0):.1f}",
                f"{bt_data.get('mean_clv_pct', 0):.2f}",
                f"{bt_data.get('total_pnl_units', 0):.1f}",
            ],
            "Paper": [
                paper_data.get("total_bets", 0),
                f"{paper_data.get('roi_per_bet', 0) * 100:.2f}%",
                f"{paper_data.get('win_rate', 0) * 100:.1f}%",
                f"{paper_data.get('profit_factor', 0):.2f}",
                f"{paper_data.get('sharpe_proxy', 0):.2f}",
                f"{paper_data.get('max_drawdown_units', 0):.1f}",
                f"{paper_data.get('mean_clv_pct', 0):.2f}",
                f"{paper_data.get('total_pnl_units', 0):.1f}",
            ],
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        # Correlation and divergence
        corr = paper_comp.get("correlation", 0)
        div_roi = paper_comp.get("divergence_roi_pct", 0)
        all_pass = paper_comp.get("all_pass", False)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Correlation", f"{corr:.4f}",
                       delta="High" if corr > 0.99 else "Low")
        with c2:
            st.metric("ROI Divergence", f"{div_roi:.1f}%",
                       delta="Concerning" if abs(div_roi) > 10 else "Acceptable")
        with c3:
            st.metric("Validation", "PASSED" if all_pass else "FAILED",
                       delta="Ready for live" if all_pass else "Needs review")

    # ── Baseline vs Tier B from backtests ──
    st.markdown("---")
    st.subheader("Baseline vs Tier B Equity Comparison")

    if backtests:
        # Separate backtests with/without Tier B
        tier_b_on = [bt for bt in backtests if bt.get("tier_b", {}).get("sharp") or bt.get("tier_b", {}).get("dynamic_ev")]
        tier_b_off = [bt for bt in backtests if not bt.get("tier_b", {}).get("sharp") and not bt.get("tier_b", {}).get("dynamic_ev")]

        # If all have Tier B on, simulate baseline by using paper comparison
        if tier_b_on and not tier_b_off:
            # Use paper comparison as baseline proxy
            if paper_comp:
                bt_pnl = paper_comp.get("backtest", {}).get("total_pnl_units", 0)
                paper_pnl = paper_comp.get("paper", {}).get("total_pnl_units", 0)

                # Build synthetic equity curves
                baseline_bankroll = _build_synthetic_equity(paper_pnl, len(tier_b_on))
                tier_b_bankroll = _build_synthetic_equity(bt_pnl, len(tier_b_on))

                dates = [bt.get("end_date", f"Period {i+1}") for i, bt in enumerate(tier_b_on)]

                fig = baseline_vs_tier_b_comparison(
                    dates, baseline_bankroll, dates, tier_b_bankroll,
                    title="Paper Trading (Baseline) vs Backtest (Tier B)",
                    dark=dark,
                )
                fig.update_layout(**ptemplate)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Just show Tier B equity
                cum_pnl = 0.0
                dates_tb = []
                bankroll_tb = []
                for bt in tier_b_on:
                    cum_pnl += bt.get("total_pnl_units", 0)
                    dates_tb.append(bt.get("end_date", "?"))
                    bankroll_tb.append(1000.0 + cum_pnl)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates_tb, y=bankroll_tb, mode="lines+markers",
                    name="Tier B Equity",
                    line=dict(color="#58a6ff" if dark else "#1f77b4", width=2.5),
                ))
                fig.add_hline(y=1000, line_dash="dash",
                               line_color="#f85149" if dark else "#d62728",
                               annotation_text="Starting bankroll")
                fig.update_layout(
                    title="Tier B Equity Curve",
                    xaxis_title="Period", yaxis_title="Bankroll",
                    **ptemplate,
                )
                st.plotly_chart(fig, use_container_width=True)
        elif tier_b_off and tier_b_on:
            # Both exist — compare directly
            cum_pnl_base = 0.0
            cum_pnl_tier = 0.0
            dates_base = []
            bankroll_base = []
            dates_tier = []
            bankroll_tier = []

            for bt in tier_b_off:
                cum_pnl_base += bt.get("total_pnl_units", 0)
                dates_base.append(bt.get("end_date", "?"))
                bankroll_base.append(1000.0 + cum_pnl_base)

            for bt in tier_b_on:
                cum_pnl_tier += bt.get("total_pnl_units", 0)
                dates_tier.append(bt.get("end_date", "?"))
                bankroll_tier.append(1000.0 + cum_pnl_tier)

            fig = baseline_vs_tier_b_comparison(
                dates_base, bankroll_base, dates_tier, bankroll_tier,
                title="Baseline vs Tier B — Cumulative Equity",
                dark=dark,
            )
            fig.update_layout(**ptemplate)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No Tier B data available for comparison")
    else:
        st.info("No backtest data available for comparison")

    # ── Metrics comparison chart ──
    if backtests:
        st.subheader("Key Metrics Comparison")
        metrics_data = []
        for bt in backtests:
            tier_b = bt.get("tier_b", {})
            label = "Tier B" if (tier_b.get("sharp") or tier_b.get("dynamic_ev")) else "Baseline"
            metrics_data.append({
                "Period": bt.get("start_date", "?"),
                "Strategy": label,
                "ROI %": bt.get("roi_per_bet", 0) * 100,
                "Win Rate %": bt.get("win_rate", 0) * 100,
                "CLV %": bt.get("mean_clv_pct", 0),
                "Sharpe": bt.get("sharpe_proxy", 0),
                "Max DD": bt.get("max_drawdown_units", 0),
            })

        if metrics_data:
            mdf = pd.DataFrame(metrics_data)
            # Grouped bar chart for ROI comparison
            import plotly.express as px
            fig_metrics = px.bar(
                mdf, x="Period", y="ROI %", color="Strategy",
                barmode="group",
                title="ROI by Strategy and Period",
                color_discrete_map={"Tier B": "#58a6ff" if dark else "#1f77b4",
                                     "Baseline": "#8b949e" if dark else "#7f7f7f"},
            )
            fig_metrics.update_layout(**ptemplate)
            st.plotly_chart(fig_metrics, use_container_width=True)


def _build_synthetic_equity(total_pnl: float, n_periods: int) -> list[float]:
    """Build a synthetic equity curve from total PnL spread across periods."""
    if n_periods == 0:
        return [1000.0]
    per_period = total_pnl / n_periods
    return [1000.0 + per_period * (i + 1) for i in range(n_periods)]
