"""
CLV and ROI evaluation metrics for model training and validation.

Provides custom eval_metric functions for XGBoost and standalone
metric computation for walk-forward validation.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np


def clv_eval_metric(
    preds: np.ndarray,
    dtrain: Any,
) -> Tuple[str, float]:
    """
    XGBoost custom evaluation metric based on CLV.

    Returns a score where higher is better (XGBoost convention for eval_metric).
    Measures the correlation between predicted edge and realized CLV.

    Usage:
        model = xgb.train(
            params={...},
            dtrain=dtrain,
            evals=[(dval, 'val')],
            obj=clv_xgb_objective,
            custom_metric=clv_eval_metric,
        )
    """
    opening_odds = dtrain.get_float_info('opening_odds')
    closing_odds = dtrain.get_float_info('closing_odds')

    preds_prob = 1.0 / (1.0 + np.exp(-preds))

    predicted_edge = preds_prob - (1.0 / opening_odds)
    realized_clv = np.log(closing_odds) - np.log(opening_odds)

    # Correlation between predicted edge and realized CLV
    # High correlation = our edge predictions align with market movement
    if np.std(predicted_edge) < 1e-8 or np.std(realized_clv) < 1e-8:
        return 'clv_corr', 0.0

    correlation = np.corrcoef(predicted_edge, realized_clv)[0, 1]
    return 'clv_corr', float(correlation) if not np.isnan(correlation) else 0.0


def roi_at_k(
    predictions: np.ndarray,
    labels: np.ndarray,
    odds: np.ndarray,
    k: int = 50,
    commission_rate: float = 0.05,
    min_edge: float = 0.03,
) -> Dict[str, float]:
    """
    Calculate ROI on the top-k value bets (highest predicted edge).

    This is the most realistic metric: only bet when we detect edge,
    and measure actual profitability.

    Args:
        predictions: Model predicted probabilities
        labels: Actual outcomes (1=win, 0=loss)
        odds: Decimal odds available at bet time
        k: Number of top bets to evaluate
        commission_rate: Exchange commission (0.05 = 5%)
        min_edge: Minimum edge to consider a bet

    Returns:
        Dict with roi, win_rate, avg_edge, bets_placed, profit
    """
    implied_probs = 1.0 / odds
    edges = predictions - implied_probs

    # Only consider bets above minimum edge
    bet_mask = edges > min_edge
    if not np.any(bet_mask):
        return {"roi": 0.0, "win_rate": 0.0, "avg_edge": 0.0, "bets_placed": 0, "profit": 0.0}

    # Sort by edge (descending) and take top-k
    bet_indices = np.where(bet_mask)[0]
    sorted_indices = bet_indices[np.argsort(-edges[bet_mask])]
    top_k_indices = sorted_indices[:k]

    if len(top_k_indices) == 0:
        return {"roi": 0.0, "win_rate": 0.0, "avg_edge": 0.0, "bets_placed": 0, "profit": 0.0}

    # Calculate P&L with unit stakes
    total_stake = float(len(top_k_indices))
    total_return = 0.0
    wins = 0

    for idx in top_k_indices:
        won = labels[idx] == 1
        if won:
            gross_profit = odds[idx] - 1.0
            commission = gross_profit * commission_rate
            total_return += 1.0 + gross_profit - commission
            wins += 1
        else:
            total_return += 0.0  # Lost the stake

    profit = total_return - total_stake
    roi = profit / total_stake if total_stake > 0 else 0.0

    return {
        "roi": round(float(roi), 6),
        "win_rate": round(float(wins / len(top_k_indices)), 4),
        "avg_edge": round(float(np.mean(edges[top_k_indices])), 6),
        "bets_placed": int(len(top_k_indices)),
        "profit": round(float(profit), 4),
    }


def sharpe_ratio(
    returns: np.ndarray,
    annualize: bool = True,
    risk_free_rate: float = 0.0,
    trading_days: int = 365,
) -> float:
    """
    Calculate Sharpe ratio of bet returns.

    Args:
        returns: Array of per-bet returns (e.g., +0.10, -1.00, +0.50)
        annualize: If True, multiply by sqrt(trading_days)
        risk_free_rate: Annual risk-free rate
        trading_days: Number of trading days per year for annualization
    """
    if len(returns) < 2:
        return 0.0

    mean_return = np.mean(returns)
    std_return = np.std(returns)

    if std_return < 1e-10:
        return 0.0

    sharpe = (mean_return - risk_free_rate / trading_days) / std_return

    if annualize:
        sharpe *= np.sqrt(trading_days)

    return float(sharpe)


def sortino_ratio(
    returns: np.ndarray,
    annualize: bool = True,
    min_acceptable_return: float = 0.0,
    trading_days: int = 365,
) -> float:
    """
    Calculate Sortino ratio — penalizes only downside volatility.

    More appropriate than Sharpe for betting returns which are asymmetric.
    """
    if len(returns) < 2:
        return 0.0

    mean_return = np.mean(returns)
    downside = returns[returns < min_acceptable_return]

    if len(downside) == 0:
        return float('inf') if mean_return > 0 else 0.0

    downside_std = np.sqrt(np.mean((downside - min_acceptable_return) ** 2))

    if downside_std < 1e-10:
        return 0.0

    sortino = (mean_return - min_acceptable_return) / downside_std

    if annualize:
        sortino *= np.sqrt(trading_days)

    return float(sortino)


def calmar_ratio(
    returns: np.ndarray,
    trading_days: int = 365,
) -> float:
    """
    Calculate Calmar ratio — annualized return / maximum drawdown.

    High Calmar = good returns with controlled drawdowns.
    """
    if len(returns) < 2:
        return 0.0

    # Calculate equity curve
    equity = np.cumsum(returns) + 1.0  # Start at 1.0

    # Maximum drawdown
    peak = np.maximum.accumulate(equity)
    drawdowns = (peak - equity) / peak
    max_drawdown = float(np.max(drawdowns))

    if max_drawdown < 1e-10:
        return float('inf')

    # Annualized return
    total_return = equity[-1] - 1.0
    n_days = len(returns)
    annualized_return = total_return * (trading_days / n_days) if n_days > 0 else 0.0

    return float(annualized_return / max_drawdown)


def evaluate_model_clv(
    predictions: np.ndarray,
    labels: np.ndarray,
    opening_odds: np.ndarray,
    closing_odds: np.ndarray,
    commission_rate: float = 0.05,
    min_edge: float = 0.03,
) -> Dict[str, float]:
    """
    Comprehensive CLV-based model evaluation.

    Combines all metrics into a single report for model comparison.
    """
    # CLV correlation
    predicted_edge = predictions - (1.0 / opening_odds)
    realized_clv = np.log(closing_odds) - np.log(opening_odds)

    if np.std(predicted_edge) > 1e-8 and np.std(realized_clv) > 1e-8:
        clv_corr = float(np.corrcoef(predicted_edge, realized_clv)[0, 1])
    else:
        clv_corr = 0.0

    # Beat closing line rate
    beat_closing = np.mean(predicted_edge > 0) if len(predicted_edge) > 0 else 0.0

    # ROI metrics
    roi_result = roi_at_k(predictions, labels, opening_odds, k=50,
                          commission_rate=commission_rate, min_edge=min_edge)

    # Simulated returns for Sharpe/Sortino/Calmar
    bet_mask = predicted_edge > min_edge
    sim_returns = []
    for i in range(len(predictions)):
        if bet_mask[i]:
            if labels[i] == 1:
                gross = opening_odds[i] - 1.0
                net = gross * (1.0 - commission_rate)
                sim_returns.append(net)  # Profit as fraction of stake
            else:
                sim_returns.append(-1.0)  # Lost stake

    sim_returns = np.array(sim_returns) if sim_returns else np.array([0.0])

    return {
        "clv_correlation": round(clv_corr, 6),
        "beat_closing_line_rate": round(float(beat_closing), 4),
        "avg_predicted_edge": round(float(np.mean(predicted_edge)), 6),
        "roi_top50": roi_result["roi"],
        "roi_bets_placed": roi_result["bets_placed"],
        "roi_profit": roi_result["profit"],
        "sharpe": round(sharpe_ratio(sim_returns), 4),
        "sortino": round(sortino_ratio(sim_returns), 4),
        "calmar": round(calmar_ratio(sim_returns), 4),
        "total_value_bets": int(np.sum(bet_mask)),
    }
