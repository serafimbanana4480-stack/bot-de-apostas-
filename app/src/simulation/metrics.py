"""Extended backtest metrics: Sharpe, Sortino, profit factor, drawdown."""
from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def compute_backtest_metrics(bets_df: pd.DataFrame, pnl_col: str = "pnl_units") -> Dict[str, Any]:
    if bets_df.empty:
        return {}

    pnl = bets_df[pnl_col].astype(float)
    cumulative = pnl.cumsum()
    peak = cumulative.cummax()
    dd = (peak - cumulative) / peak.replace(0, np.nan)
    max_dd = float(dd.max()) if len(dd) else 0.0

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = wins.sum() if len(wins) else 0.0
    gross_loss = abs(losses.sum()) if len(losses) else 1e-9

    mean_r = pnl.mean()
    std_r = pnl.std() if len(pnl) > 1 else 1e-9
    downside = pnl[pnl < 0]
    down_std = downside.std() if len(downside) > 1 else 1e-9

    return {
        "total_bets": len(bets_df),
        "roi_per_bet": round(float(mean_r), 4),
        "total_pnl_units": round(float(pnl.sum()), 2),
        "win_rate": round(float((pnl > 0).mean()), 4),
        "profit_factor": round(float(gross_profit / gross_loss), 4),
        "sharpe_proxy": round(float(mean_r / std_r * np.sqrt(len(pnl))), 4) if std_r > 0 else 0.0,
        "sortino_proxy": round(float(mean_r / down_std * np.sqrt(len(pnl))), 4) if down_std > 0 else 0.0,
        "max_drawdown_units": round(max_dd, 4),
        "mean_clv_pct": round(float(bets_df["clv_pct"].mean() * 100), 4) if "clv_pct" in bets_df.columns else None,
        "pct_positive_clv": round(float((bets_df["clv_pct"] > 0).mean() * 100), 2) if "clv_pct" in bets_df.columns else None,
    }
