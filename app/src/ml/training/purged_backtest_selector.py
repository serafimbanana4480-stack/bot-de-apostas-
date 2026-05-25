"""
Purged backtest validation during training — selects the model checkpoint
that maximizes real ROI, not just theoretical CLV.

Problem: Current validation uses CLV correlation as the primary metric,
but CLV correlation doesn't guarantee actual profitability.

Solution: For each training checkpoint (boosting round), run a purged
backtest on the validation fold. Select the checkpoint that maximizes
ROI (or Sharpe, or any user-chosen metric) on the validation set.

This bridges the gap between "beating the closing line" and "making money."

Usage:
    from src.ml.training.purged_backtest_selector import PurgedBacktestSelector

    selector = PurgedBacktestSelector(
        metric="roi",  # or "sharpe", "sortino", "calmar"
        min_edge=0.03,
        commission_rate=0.05,
    )
    best_round = selector.select(dtrain, dval, params, max_rounds=200)
    model = xgb.train(params, dtrain, best_round, ...)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import xgboost as xgb

from src.ml.training.clv_metrics import (
    calmar_ratio,
    sharpe_ratio,
    sortino_ratio,
)
from src.ml.training.clv_objective import clv_xgb_objective

logger = logging.getLogger("purged_backtest_selector")


class PurgedBacktestSelector:
    """
    Selects the best XGBoost checkpoint based on purged backtest performance.

    Instead of using the default early stopping (which minimizes log-loss or
    a custom eval metric), this selector evaluates each checkpoint with a
    full backtest simulation and picks the one that maximizes a chosen metric.
    """

    def __init__(
        self,
        metric: str = "roi",
        min_edge: float = 0.03,
        commission_rate: float = 0.05,
        k_roi: int = 50,
        stake_fraction: float = 0.02,
        initial_bankroll: float = 1000.0,
    ):
        """
        Args:
            metric: Metric to optimize ("roi", "sharpe", "sortino", "calmar")
            min_edge: Minimum edge to place a bet
            commission_rate: Exchange commission rate
            k_roi: Top-k bets for ROI evaluation
            stake_fraction: Fraction of bankroll per bet
            initial_bankroll: Starting bankroll for simulation
        """
        self.metric = metric
        self.min_edge = min_edge
        self.commission_rate = commission_rate
        self.k_roi = k_roi
        self.stake_fraction = stake_fraction
        self.initial_bankroll = initial_bankroll

    def _simulate_backtest(
        self,
        predictions: np.ndarray,
        labels: np.ndarray,
        odds: np.ndarray,
    ) -> Dict[str, float]:
        """
        Run a full backtest simulation on validation predictions.

        Simulates Kelly-like staking and computes ROI, Sharpe, etc.
        """
        implied = 1.0 / odds
        edges = predictions - implied

        bankroll = self.initial_bankroll
        returns = []
        bets_placed = 0

        for i in range(len(predictions)):
            if edges[i] > self.min_edge and bankroll > 0:
                stake = bankroll * self.stake_fraction
                if labels[i] == 1:
                    gross = odds[i] - 1.0
                    commission = gross * self.commission_rate
                    pnl = stake * (gross - commission)
                else:
                    pnl = -stake

                bankroll += pnl
                returns.append(pnl / self.initial_bankroll)
                bets_placed += 1

        if not returns:
            return {"roi": 0.0, "sharpe": 0.0, "sortino": 0.0, "calmar": 0.0, "bets": 0}

        returns = np.array(returns)
        roi = (bankroll - self.initial_bankroll) / self.initial_bankroll
        sharpe = sharpe_ratio(returns, annualize=False)
        sortino = sortino_ratio(returns, annualize=False)
        calmar_val = calmar_ratio(returns)

        return {
            "roi": round(roi, 6),
            "sharpe": round(sharpe, 4),
            "sortino": round(sortino, 4),
            "calmar": round(calmar_val, 4),
            "bets": bets_placed,
            "final_bankroll": round(bankroll, 2),
        }

    def select(
        self,
        dtrain: xgb.DMatrix,
        dval: xgb.DMatrix,
        params: Dict[str, Any],
        max_rounds: int = 200,
        eval_freq: int = 10,
        objective: str = "logloss",
    ) -> int:
        """
        Train with checkpointing and select the best round based on backtest.

        Args:
            dtrain: Training DMatrix
            dval: Validation DMatrix
            params: XGBoost parameters
            max_rounds: Maximum boosting rounds
            eval_freq: Evaluate backtest every N rounds
            objective: XGBoost objective ("logloss" or "clv")

        Returns:
            Best number of boosting rounds
        """
        labels = dval.get_label()
        odds_val = dval.get_float_info("opening_odds") if dval.get_float_info("opening_odds") is not None else np.ones(len(labels)) * 2.0

        best_round = max_rounds
        best_score = -np.inf
        checkpoint_scores = []

        # Train incrementally, evaluating backtest at each checkpoint
        prev_model = None
        for round_idx in range(eval_freq, max_rounds + 1, eval_freq):
            if objective == "clv":
                model = xgb.train(
                    params=params,
                    dtrain=dtrain,
                    num_boost_round=round_idx,
                    obj=clv_xgb_objective,
                    xgb_model=prev_model,
                    verbose_eval=False,
                )
                raw_preds = model.predict(dval)
                preds = 1.0 / (1.0 + np.exp(-raw_preds))
            else:
                model = xgb.train(
                    params=params,
                    dtrain=dtrain,
                    num_boost_round=round_idx,
                    xgb_model=prev_model,
                    verbose_eval=False,
                )
                raw_preds = model.predict(dval)
                preds = 1.0 / (1.0 + np.exp(-raw_preds))

            prev_model = model

            # Evaluate with backtest
            bt_result = self._simulate_backtest(preds, labels, odds_val)
            score = bt_result.get(self.metric, 0.0)

            checkpoint_scores.append({
                "round": round_idx,
                "score": score,
                "metrics": bt_result,
            })

            if score > best_score:
                best_score = score
                best_round = round_idx

        logger.info(
            "Purged backtest selector: best_round=%d, %s=%.4f (evaluated %d checkpoints)",
            best_round, self.metric, best_score, len(checkpoint_scores),
        )

        return best_round

    def kelly_sweep(
        self,
        predictions: np.ndarray,
        labels: np.ndarray,
        odds: np.ndarray,
        kelly_multipliers: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Sweep different Kelly multiplier values and find the one that
        maximizes the chosen metric on the validation set.

        Instead of using a fixed Kelly multiplier (e.g., 0.25), this
        tests multiple values and selects the one that produces the best
        risk-adjusted returns.

        Args:
            predictions: Model predicted probabilities
            labels: True outcomes
            odds: Decimal odds
            kelly_multipliers: List of Kelly fractions to test

        Returns:
            Dict with best_kelly, all results, and best metrics
        """
        if kelly_multipliers is None:
            kelly_multipliers = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

        results = []
        best_score = -np.inf
        best_kelly = 0.25

        for k_frac in kelly_multipliers:
            # Override stake fraction temporarily
            original_stake = self.stake_fraction
            self.stake_fraction = k_frac

            bt_result = self._simulate_backtest(predictions, labels, odds)
            score = bt_result.get(self.metric, 0.0)

            self.stake_fraction = original_stake

            results.append({
                "kelly_multiplier": k_frac,
                "metric_value": score,
                "metrics": bt_result,
            })

            if score > best_score:
                best_score = score
                best_kelly = k_frac

        logger.info(
            "Kelly sweep: best_kelly=%.2f, %s=%.4f (tested %s)",
            best_kelly, self.metric, best_score, kelly_multipliers,
        )

        return {
            "best_kelly": best_kelly,
            "best_score": best_score,
            "best_metrics": next(r["metrics"] for r in results if r["kelly_multiplier"] == best_kelly),
            "all_results": results,
            "metric": self.metric,
        }

    def select_from_history(
        self,
        evals_result: Dict[str, List[float]],
        predictions_per_round: List[np.ndarray],
        labels: np.ndarray,
        odds: np.ndarray,
    ) -> int:
        """
        Select best round from pre-computed evaluation history.

        Useful when you already have predictions at each round.
        """
        best_round = 1
        best_score = -np.inf

        for round_idx, preds in enumerate(predictions_per_round, 1):
            bt_result = self._simulate_backtest(preds, labels, odds)
            score = bt_result.get(self.metric, 0.0)

            if score > best_score:
                best_score = score
                best_round = round_idx

        return best_round
