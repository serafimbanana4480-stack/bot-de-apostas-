"""CLV Analysis page — trend charts, breakdown by league/market, heatmap."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from .loaders import load_clv_report, load_backtest_reports, load_data_lake
from .charts import clv_heatmap_by_league
from .theme import plotly_template


def render_clv_analysis(data_dir: str, dark: bool = True) -> None:
    """Render CLV trend analysis with breakdown by league and market."""
    st.header("CLV Analysis")

    clv = load_clv_report(data_dir)
    backtests = load_backtest_reports(data_dir)
    df = load_data_lake(data_dir)
    ptemplate = plotly_template(dark)

    if not clv and not backtests:
        st.info("No CLV data. Run: `py scripts/run_clv_report.py`")
        return

    # ── Current Edge Status ──
    st.subheader("Current Edge Status")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Mean CLV", f"{clv.get('mean_clv_pct', 0):.2f}%")
    with c2:
        st.metric("Median CLV", f"{clv.get('median_clv_pct', 0):.2f}%")
    with c3:
        st.metric("Positive CLV %", f"{clv.get('pct_positive_clv', 0):.1f}%")

    if clv.get("edge_proven"):
        st.success("Edge Proven — Model beats closing line on average")
    else:
        st.error("Edge NOT Proven — Model does NOT beat closing line")

    # ── CLV Trend Across Backtests ──
    if backtests:
        st.subheader("CLV Trend Across Backtests")
        bt_df = pd.DataFrame([
            {
                "Period": bt.get("start_date", "?"),
                "CLV": bt.get("mean_clv_pct", 0),
                "Bets": bt.get("total_bets", 0),
                "ROI": bt.get("roi_per_bet", 0) * 100,
                "Reliable": bt.get("statistical_confidence", {}).get("reliable", False),
            }
            for bt in backtests
        ])

        fig = px.scatter(
            bt_df, x="Period", y="CLV", size="Bets", color="Reliable",
            hover_data=["ROI"],
            title="CLV % by Backtest Period",
            color_discrete_map={True: "#3fb950" if dark else "#2ca02c",
                                False: "#d29922" if dark else "#ff7f0e"},
        )
        fig.add_hline(y=2.565, line_dash="dash",
                       line_color="#f85149" if dark else "#d62728",
                       annotation_text="Break-even (2.57%)")
        fig.add_hline(y=1.0, line_dash="dash",
                       line_color="#d29922" if dark else "#ff7f0e",
                       annotation_text="Minimum threshold (1%)")
        fig.update_layout(**ptemplate)
        st.plotly_chart(fig, use_container_width=True)

        # ROI vs CLV correlation
        fig2 = px.scatter(
            bt_df, x="CLV", y="ROI", size="Bets", color="Reliable",
            title="ROI vs CLV Correlation",
            trendline="ols",
        )
        fig2.update_layout(**ptemplate)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── CLV Breakdown by League (NEW) ──
    st.subheader("CLV Breakdown by League")
    if not df.empty and "league" in df.columns:
        # Compute per-match CLV
        df_clv = _compute_per_match_clv(df)
        if "clv_pct" in df_clv.columns:
            fig_league = clv_heatmap_by_league(df_clv, dark=dark)
            fig_league.update_layout(**ptemplate)
            st.plotly_chart(fig_league, use_container_width=True)

            # League stats table
            league_stats = df_clv.groupby("league").agg(
                matches=("clv_pct", "count"),
                mean_clv=("clv_pct", "mean"),
                median_clv=("clv_pct", "median"),
                pct_positive=("clv_pct", lambda x: (x > 0).mean() * 100),
            ).round(2).sort_values("mean_clv", ascending=False)
            st.dataframe(league_stats, use_container_width=True)
        else:
            st.info("Closing odds not available — cannot compute per-league CLV")
    else:
        st.info("No match data loaded for league breakdown")

    # ── CLV by Outcome Type (NEW) ──
    st.subheader("CLV by Outcome Type")
    if not df.empty and "actual_outcome" in df.columns:
        df_clv = _compute_per_match_clv(df)
        if "clv_pct" in df_clv.columns and "actual_outcome" in df_clv.columns:
            outcome_stats = df_clv.groupby("actual_outcome").agg(
                matches=("clv_pct", "count"),
                mean_clv=("clv_pct", "mean"),
                median_clv=("clv_pct", "median"),
            ).round(2)

            fig_outcome = px.bar(
                outcome_stats.reset_index(),
                x="actual_outcome", y="mean_clv",
                color="mean_clv",
                color_continuous_scale=["#f85149", "#d29922", "#3fb950"] if dark else ["#d62728", "#ff7f0e", "#2ca02c"],
                title="Mean CLV by Outcome Type (1 / X / 2)",
                labels={"actual_outcome": "Outcome", "mean_clv": "Mean CLV %"},
            )
            fig_outcome.add_hline(y=2.565, line_dash="dash",
                                   line_color="#f85149" if dark else "#d62728",
                                   annotation_text="Break-even")
            fig_outcome.update_layout(**ptemplate)
            st.plotly_chart(fig_outcome, use_container_width=True)
        else:
            st.info("Outcome/CLV data not available")
    else:
        st.info("No outcome data for breakdown")

    # ── CLV Distribution (NEW) ──
    st.subheader("CLV Distribution")
    if not df.empty:
        df_clv = _compute_per_match_clv(df)
        if "clv_pct" in df_clv.columns:
            fig_dist = px.histogram(
                df_clv, x="clv_pct", nbins=50,
                title="Distribution of CLV %",
                labels={"clv_pct": "CLV %"},
                color_discrete_sequence=["#58a6ff"] if dark else ["#1f77b4"],
            )
            fig_dist.add_vline(x=0, line_dash="dash",
                               line_color="#8b949e" if dark else "#666",
                               annotation_text="Zero CLV")
            fig_dist.add_vline(x=2.565, line_dash="dash",
                               line_color="#f85149" if dark else "#d62728",
                               annotation_text="Break-even")
            fig_dist.update_layout(**ptemplate)
            st.plotly_chart(fig_dist, use_container_width=True)


def _compute_per_match_clv(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-match CLV from opening vs closing odds."""
    df = df.copy()
    # Try different column naming conventions
    open_col = None
    close_col = None

    for o, c in [("odd_1", "closing_odd"), ("odd_1", "pin_close_home"),
                  ("open_odd_home", "pin_close_home")]:
        if o in df.columns and c in df.columns:
            open_col, close_col = o, c
            break

    if open_col and close_col:
        df["clv_pct"] = ((df[close_col] / df[open_col]) - 1) * 100
    return df
