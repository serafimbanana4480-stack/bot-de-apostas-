"""Data Explorer page — data lake, correlations, odds analysis, value bet distribution."""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from .loaders import load_data_lake
from .state import get_state
from .theme import plotly_template
from .export_utils import export_csv_button


def render_data_explorer(data_dir: str, dark: bool = True) -> None:
    """Render data lake explorer with correlations and value bet analysis."""
    st.header("Data Explorer")

    df = load_data_lake(data_dir)
    ptemplate = plotly_template(dark)

    if df.empty:
        st.info("No data loaded. Run: `py scripts/ingest_free_data.py --source mock`")
        return

    st.subheader(f"Dataset: {len(df)} matches, {len(df.columns)} columns")

    # ── Filters (with session state persistence) ──
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if "league" in df.columns:
            default_leagues = get_state("league_filter", df["league"].unique().tolist()[:3])
            # Ensure defaults are valid
            valid_defaults = [l for l in default_leagues if l in df["league"].unique()]
            leagues = st.multiselect("Leagues", options=df["league"].unique().tolist(),
                                      default=valid_defaults, key="explorer_leagues")
            if leagues:
                df = df[df["league"].isin(leagues)]

    with col2:
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            min_date, max_date = df["date"].min().date(), df["date"].max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date), key="explorer_dates")
            if len(date_range) == 2:
                df = df[(df["date"] >= pd.Timestamp(date_range[0])) & (df["date"] <= pd.Timestamp(date_range[1]))]

    # ── Data table ──
    st.dataframe(df, use_container_width=True)
    export_csv_button(df, filename="data_explorer.csv", label="Export Filtered Data CSV")

    # ── Goals Distribution ──
    if "home_goals" in df.columns and "away_goals" in df.columns:
        st.subheader("Goals Distribution")
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            fig = px.histogram(df, x="home_goals", nbins=10,
                               color_discrete_sequence=["#58a6ff"] if dark else ["#1f77b4"],
                               opacity=0.7, title="Home Goals")
            fig.update_layout(**ptemplate)
            st.plotly_chart(fig, use_container_width=True)
        with g_col2:
            fig2 = px.histogram(df, x="away_goals", nbins=10,
                                color_discrete_sequence=["#f85149"] if dark else ["#d62728"],
                                opacity=0.7, title="Away Goals")
            fig2.update_layout(**ptemplate)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Odds Distribution ──
    if "odd_1" in df.columns:
        st.subheader("Odds Distribution")
        fig = px.box(df, y=["odd_1", "odd_X", "odd_2"], title="Match Odds Distribution",
                     color_discrete_sequence=["#58a6ff", "#d29922", "#f85149"] if dark
                     else ["#1f77b4", "#ff7f0e", "#d62728"])
        fig.update_layout(**ptemplate)
        st.plotly_chart(fig, use_container_width=True)

    # ── Opening vs Closing Odds Scatter (NEW) ──
    st.subheader("Opening vs Closing Odds")
    open_col = None
    close_col = None
    for o, c in [("odd_1", "pin_close_home"), ("open_odd_home", "pin_close_home"),
                  ("odd_1", "closing_odd")]:
        if o in df.columns and c in df.columns:
            open_col, close_col = o, c
            break

    if open_col and close_col:
        fig_oc = px.scatter(
            df, x=open_col, y=close_col,
            title="Opening vs Closing Odds (Home)",
            opacity=0.5,
            color_discrete_sequence=["#3fb950"] if dark else ["#2ca02c"],
            hover_data=["league"] if "league" in df.columns else None,
        )
        # Add 45-degree line
        min_val = min(df[open_col].min(), df[close_col].min())
        max_val = max(df[open_col].max(), df[close_col].max())
        fig_oc.add_trace(go.Scatter(
            x=[min_val, max_val], y=[min_val, max_val],
            mode="lines", name="No Movement",
            line=dict(dash="dash", color="#8b949e" if dark else "#666"),
        ))
        fig_oc.update_layout(**ptemplate)
        st.plotly_chart(fig_oc, use_container_width=True)

    # ── Correlation Matrix (NEW) ──
    st.subheader("Feature Correlation Matrix")
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    # Limit to meaningful columns
    priority_cols = [c for c in ["home_goals", "away_goals", "odd_1", "odd_X", "odd_2",
                                  "open_odd_home", "open_odd_draw", "open_odd_away",
                                  "pin_close_home", "pin_close_draw", "pin_close_away",
                                  "line_movement_home", "closing_odd"]
                     if c in numeric_cols]
    if len(priority_cols) >= 3:
        corr = df[priority_cols].corr()
        fig_corr = px.imshow(
            corr, text_auto=".2f",
            title="Correlation Matrix",
            color_continuous_scale="RdBu_r" if dark else "RdBu_r",
            aspect="auto",
        )
        fig_corr.update_layout(**ptemplate, height=500)
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Not enough numeric columns for correlation matrix")

    # ── Value Bet Distribution by EV Threshold (NEW) ──
    st.subheader("Value Bet Distribution")
    if open_col and close_col and "actual_outcome" in df.columns:
        df_vb = df.copy()
        # Simple value bet proxy: matches where closing odds > opening odds (market moved against us)
        df_vb["ev_proxy"] = ((df_vb[close_col] / df_vb[open_col]) - 1) * 100

        ev_threshold = st.slider("EV Threshold %", -10.0, 20.0, 1.0, 0.5, key="ev_threshold")
        value_bets = df_vb[df_vb["ev_proxy"] > ev_threshold]

        fig_ev = px.histogram(
            df_vb, x="ev_proxy", nbins=50,
            title=f"EV Proxy Distribution (threshold: {ev_threshold}%)",
            labels={"ev_proxy": "EV Proxy %"},
            color_discrete_sequence=["#3fb950"] if dark else ["#2ca02c"],
        )
        fig_ev.add_vline(x=ev_threshold, line_dash="dash",
                          line_color="#f85149" if dark else "#d62728",
                          annotation_text=f"Threshold: {ev_threshold}%")
        fig_ev.update_layout(**ptemplate)
        st.plotly_chart(fig_ev, use_container_width=True)

        st.metric("Value Bets Above Threshold", f"{len(value_bets)} / {len(df_vb)}",
                   delta=f"{len(value_bets) / max(len(df_vb), 1) * 100:.1f}%")

    # ── Exposure by League (NEW) ──
    st.subheader("Exposure by League")
    if "league" in df.columns:
        league_counts = df["league"].value_counts()
        fig_pie = px.pie(
            values=league_counts.values,
            names=league_counts.index,
            title="Match Distribution by League",
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )
        fig_pie.update_layout(**ptemplate)
        st.plotly_chart(fig_pie, use_container_width=True)
