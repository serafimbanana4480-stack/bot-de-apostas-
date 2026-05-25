"""Reusable chart builders — equity curve, drawdown, gauges, heatmaps."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def equity_curve_with_drawdown(
    dates: pd.Series | list,
    bankroll: pd.Series | list,
    title: str = "Equity Curve & Drawdown",
    dark: bool = True,
    starting_bankroll: float = 1000.0,
) -> go.Figure:
    """Build equity curve with drawdown shading.

    Green fill above starting bankroll, red fill below (drawdown zone).
    """
    dates = list(dates)
    bankroll = list(bankroll)

    # Compute drawdown series
    peak = np.maximum.accumulate(bankroll)
    drawdown = [(b - p) / p * 100 for b, p in zip(bankroll, peak)]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=(title, "Drawdown %"),
    )

    # Equity line
    fig.add_trace(
        go.Scatter(
            x=dates, y=bankroll, mode="lines", name="Bankroll",
            line=dict(color="#3fb950" if dark else "#2ca02c", width=2.5),
            fill="tonexty",
            fillcolor="rgba(63,185,80,0.08)" if dark else "rgba(44,160,44,0.08)",
        ),
        row=1, col=1,
    )

    # Starting bankroll reference line
    fig.add_hline(
        y=starting_bankroll, line_dash="dash",
        line_color="#f85149" if dark else "#d62728",
        annotation_text=f"Start: {starting_bankroll:.0f}",
        row=1, col=1,
    )

    # Peak line
    fig.add_trace(
        go.Scatter(
            x=dates, y=peak, mode="lines", name="Peak",
            line=dict(color="#58a6ff" if dark else "#1f77b4", width=1, dash="dot"),
        ),
        row=1, col=1,
    )

    # Drawdown area
    dd_color = "#f85149" if dark else "#d62728"
    fig.add_trace(
        go.Scatter(
            x=dates, y=drawdown, mode="lines", name="Drawdown %",
            line=dict(color=dd_color, width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba(248,81,73,0.15)" if dark else "rgba(214,39,40,0.15)",
        ),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_color="#30363d" if dark else "#ccc", row=2, col=1)

    fig.update_yaxes(title_text="Bankroll", row=1, col=1)
    fig.update_yaxes(title_text="DD %", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    return fig


def baseline_vs_tier_b_comparison(
    baseline_dates: list,
    baseline_bankroll: list,
    tier_b_dates: list,
    tier_b_bankroll: list,
    title: str = "Baseline vs Tier B — Equity Comparison",
    dark: bool = True,
    starting_bankroll: float = 1000.0,
) -> go.Figure:
    """Side-by-side equity curves for Baseline and Tier B strategies."""
    fig = go.Figure()

    baseline_color = "#8b949e" if dark else "#7f7f7f"
    tier_b_color = "#58a6ff" if dark else "#1f77b4"

    fig.add_trace(go.Scatter(
        x=baseline_dates, y=baseline_bankroll,
        mode="lines", name="Baseline",
        line=dict(color=baseline_color, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=tier_b_dates, y=tier_b_bankroll,
        mode="lines", name="Tier B (Sharp + Dynamic EV)",
        line=dict(color=tier_b_color, width=2.5),
    ))

    fig.add_hline(
        y=starting_bankroll, line_dash="dash",
        line_color="#f85149" if dark else "#d62728",
        annotation_text=f"Start: {starting_bankroll:.0f}",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Bankroll",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def roi_gauge(
    roi: float,
    target_roi: float = 5.0,
    title: str = "Current ROI vs Target",
    dark: bool = True,
) -> go.Figure:
    """Speedometer/gauge chart for ROI vs target."""
    max_val = max(abs(roi), target_roi) * 2
    max_val = max(max_val, 10)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=roi,
        delta={"reference": target_roi, "increasing": {"color": "#3fb950"}, "decreasing": {"color": "#f85149"}},
        title={"text": title, "font": {"size": 16}},
        gauge={
            "axis": {"range": [-max_val, max_val], "tickfont": {"color": "#8b949e" if dark else "#555"}},
            "bar": {"color": "#3fb950" if roi >= 0 else "#f85149"},
            "steps": [
                {"range": [-max_val, 0], "color": "rgba(248,81,73,0.15)"},
                {"range": [0, target_roi], "color": "rgba(210,153,34,0.15)"},
                {"range": [target_roi, max_val], "color": "rgba(63,185,80,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#d29922", "width": 3},
                "thickness": 0.8,
                "value": target_roi,
            },
        },
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=60, b=20))
    return fig


def daily_activity_heatmap(
    dates: list[str],
    values: list[int],
    title: str = "Daily Activity (GitHub-style)",
    dark: bool = True,
) -> go.Figure:
    """GitHub contribution-graph style heatmap of daily betting activity."""
    df = pd.DataFrame({"date": pd.to_datetime(dates), "value": values})
    df["dow"] = df["date"].dt.dayofweek   # 0=Mon
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year

    # Pivot for heatmap
    pivot = df.pivot_table(index="dow", columns="week", values="value", aggfunc="sum", fill_value=0)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"W{w}" for w in pivot.columns],
        y=day_labels[:len(pivot.index)],
        colorscale=[
            [0, "#161b22" if dark else "#f0f0f0"],
            [0.25, "#0e4429" if dark else "#c6e48b"],
            [0.5, "#006d32" if dark else "#7bc96f"],
            [0.75, "#26a641" if dark else "#239a3b"],
            [1, "#39d353" if dark else "#196127"],
        ],
        showscale=True,
        hovertemplate="Week %{x}, %{y}: %{z} bets<extra></extra>",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Week",
        yaxis_title="Day",
        height=200,
    )
    return fig


def clv_heatmap_by_league(
    df: pd.DataFrame,
    league_col: str = "league",
    clv_col: str = "clv_pct",
    dark: bool = True,
    title: str = "CLV % by League",
) -> go.Figure:
    """Heatmap of average CLV by league (and optionally market/outcome)."""
    if league_col not in df.columns or clv_col not in df.columns:
        return go.Figure().add_annotation(text="No CLV/league data available")

    agg = df.groupby(league_col)[clv_col].mean().sort_values(ascending=False)

    fig = go.Figure(go.Bar(
        x=agg.values,
        y=agg.index,
        orientation="h",
        marker_color=[
            "#3fb950" if v > 2.565 else "#d29922" if v > 1.0 else "#f85149"
            for v in agg.values
        ] if dark else [
            "#2ca02c" if v > 2.565 else "#ff7f0e" if v > 1.0 else "#d62728"
            for v in agg.values
        ],
    ))
    fig.add_vline(x=2.565, line_dash="dash", line_color="#f85149" if dark else "#d62728",
                  annotation_text="Break-even")
    fig.add_vline(x=1.0, line_dash="dash", line_color="#d29922" if dark else "#ff7f0e",
                  annotation_text="Min threshold")
    fig.update_layout(
        title=title,
        xaxis_title="Mean CLV %",
        yaxis_title="League",
        height=max(300, len(agg) * 30),
    )
    return fig
