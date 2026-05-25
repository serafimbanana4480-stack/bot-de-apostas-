"""
Window policy selector — automatically chooses between expanding and rolling
training windows based on which produces better validation metrics.

Problem: Fixed walk-forward uses a rolling window (e.g., 180 days), but
some sports/markets benefit from an expanding window (all history) while
others need rolling (forget old data). The optimal choice depends on
how fast the market changes.

Solution: Train with both policies, compare on validation, and select
the best. A meta-classifier can also learn which policy works best
for each sport/regime.

Usage:
    from src.ml.training.window_policy import WindowPolicySelector

    selector = WindowPolicySelector(policy="auto")
    result = selector.select(df, sport="football")
    # result["best_policy"] == "expanding" or "rolling"
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

logger = logging.getLogger("window_policy")


class WindowPolicy:
    """Training window policies."""
    EXPANDING = "expanding"   # Use all available history
    ROLLING = "rolling"       # Use only last N days
    AUTO = "auto"             # Automatically select best


class WindowPolicySelector:
    """
    Compares expanding vs rolling training windows and selects the best.

    For each policy:
    1. Run walk-forward validation with that window type
    2. Compute average validation metric across folds
    3. Select the policy with the best average metric

    The AUTO policy runs both and picks the winner.
    """

    def __init__(
        self,
        policy: str = "auto",
        rolling_window_days: int = 365,
        test_window_days: int = 30,
        min_train_samples: int = 50,
        metric: str = "brier",  # "brier", "roi", "sharpe"
        min_edge: float = 0.03,
        commission_rate: float = 0.05,
    ):
        self.policy = policy
        self.rolling_window_days = rolling_window_days
        self.test_window_days = test_window_days
        self.min_train_samples = min_train_samples
        self.metric = metric
        self.min_edge = min_edge
        self.commission_rate = commission_rate

    def _make_splits_expanding(
        self, df: pd.DataFrame, date_col: str,
    ) -> List[Dict[str, pd.DataFrame]]:
        """Create expanding window splits (all history up to test start)."""
        if not np.issubdtype(df[date_col].dtype, np.datetime64):
            df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)

        min_date = df[date_col].min()
        max_date = df[date_col].max()
        splits = []
        current_test_start = min_date + timedelta(days=self.rolling_window_days)

        while current_test_start < max_date:
            current_test_end = current_test_start + timedelta(days=self.test_window_days)

            train_mask = df[date_col] < current_test_start
            test_mask = (df[date_col] >= current_test_start) & (df[date_col] < current_test_end)

            train_set = df[train_mask]
            test_set = df[test_mask]

            if len(train_set) >= self.min_train_samples and not test_set.empty:
                splits.append({"train": train_set, "test": test_set})

            current_test_start = current_test_end

        return splits

    def _make_splits_rolling(
        self, df: pd.DataFrame, date_col: str,
    ) -> List[Dict[str, pd.DataFrame]]:
        """Create rolling window splits (only last N days of history)."""
        if not np.issubdtype(df[date_col].dtype, np.datetime64):
            df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)

        min_date = df[date_col].min()
        max_date = df[date_col].max()
        splits = []
        current_test_start = min_date + timedelta(days=self.rolling_window_days)

        while current_test_start < max_date:
            current_test_end = current_test_start + timedelta(days=self.test_window_days)
            train_cutoff = current_test_start - timedelta(days=self.rolling_window_days)

            train_mask = (df[date_col] >= train_cutoff) & (df[date_col] < current_test_start)
            test_mask = (df[date_col] >= current_test_start) & (df[date_col] < current_test_end)

            train_set = df[train_mask]
            test_set = df[test_mask]

            if len(train_set) >= self.min_train_samples and not test_set.empty:
                splits.append({"train": train_set, "test": test_set})

            current_test_start = current_test_end

        return splits

    def _evaluate_splits(
        self,
        splits: List[Dict[str, pd.DataFrame]],
        fit_fn: Callable,
        predict_fn: Callable,
    ) -> Dict[str, float]:
        """Evaluate a set of splits with the given model functions."""
        fold_scores = []

        for split in splits:
            train_df = split["train"]
            test_df = split["test"]

            try:
                model = fit_fn(train_df)
                preds_df = predict_fn(model, test_df)

                if self.metric == "brier" and "prob_1" in preds_df.columns and "actual_outcome" in preds_df.columns:
                    score = brier_score_loss(
                        preds_df["actual_outcome"].values,
                        preds_df["prob_1"].values,
                    )
                    fold_scores.append(score)  # Lower is better
                elif self.metric in ("roi", "sharpe"):
                    roi = self._compute_roi(preds_df)
                    if self.metric == "roi":
                        fold_scores.append(roi)  # Higher is better
                    else:
                        sharpe = self._compute_sharpe(preds_df)
                        fold_scores.append(sharpe)
                else:
                    if "prob_1" in preds_df.columns and "actual_outcome" in preds_df.columns:
                        score = brier_score_loss(
                            preds_df["actual_outcome"].values,
                            preds_df["prob_1"].values,
                        )
                        fold_scores.append(score)
            except Exception as e:
                logger.warning("Fold evaluation failed: %s", e)
                continue

        if not fold_scores:
            return {"avg_score": float("inf"), "n_folds": 0}

        return {
            "avg_score": float(np.mean(fold_scores)),
            "std_score": float(np.std(fold_scores)),
            "n_folds": len(fold_scores),
            "min_score": float(np.min(fold_scores)),
            "max_score": float(np.max(fold_scores)),
        }

    def _compute_roi(self, preds_df: pd.DataFrame) -> float:
        """Compute ROI from predictions DataFrame."""
        if "odd_1" not in preds_df.columns or "prob_1" not in preds_df.columns:
            return 0.0
        bankroll = 1000.0
        for _, row in preds_df.iterrows():
            edge = row.get("prob_1", 0) - (1.0 / row["odd_1"]) if row["odd_1"] else 0
            if edge > self.min_edge:
                stake = bankroll * 0.02
                won = row.get("actual_outcome") == "1"
                bankroll += stake * (row["odd_1"] - 1) if won else -stake
        return (bankroll - 1000.0) / 1000.0

    def _compute_sharpe(self, preds_df: pd.DataFrame) -> float:
        """Compute Sharpe ratio from predictions DataFrame."""
        returns = []
        bankroll = 1000.0
        for _, row in preds_df.iterrows():
            edge = row.get("prob_1", 0) - (1.0 / row["odd_1"]) if row.get("odd_1") else 0
            if edge > self.min_edge:
                stake = bankroll * 0.02
                won = row.get("actual_outcome") == "1"
                pnl = stake * (row["odd_1"] - 1) if won else -stake
                returns.append(pnl / 1000.0)
                bankroll += pnl
        if not returns:
            return 0.0
        ret = np.array(returns)
        std = ret.std()
        return float(ret.mean() / std * np.sqrt(365)) if std > 1e-10 else 0.0

    def select(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
        fit_fn: Optional[Callable] = None,
        predict_fn: Optional[Callable] = None,
        sport: str = "football",
    ) -> Dict[str, Any]:
        """
        Compare expanding vs rolling windows and select the best policy.

        If policy is "expanding" or "rolling", just use that policy.
        If policy is "auto", run both and compare.
        """
        if self.policy == WindowPolicy.EXPANDING:
            splits = self._make_splits_expanding(df, date_col)
            result = self._evaluate_splits(splits, fit_fn, predict_fn)
            result["best_policy"] = "expanding"
            return result

        if self.policy == WindowPolicy.ROLLING:
            splits = self._make_splits_rolling(df, date_col)
            result = self._evaluate_splits(splits, fit_fn, predict_fn)
            result["best_policy"] = "rolling"
            return result

        # AUTO: compare both
        logger.info("Comparing expanding vs rolling window for %s", sport)

        expanding_splits = self._make_splits_expanding(df, date_col)
        rolling_splits = self._make_splits_rolling(df, date_col)

        expanding_result = self._evaluate_splits(expanding_splits, fit_fn, predict_fn)
        rolling_result = self._evaluate_splits(rolling_splits, fit_fn, predict_fn)

        # Select best (lower is better for brier, higher for roi/sharpe)
        if self.metric == "brier":
            best_policy = "expanding" if expanding_result["avg_score"] <= rolling_result["avg_score"] else "rolling"
        else:
            best_policy = "expanding" if expanding_result["avg_score"] >= rolling_result["avg_score"] else "rolling"

        logger.info(
            "Window policy comparison: expanding=%.4f (n=%d), rolling=%.4f (n=%d) → %s wins",
            expanding_result["avg_score"], expanding_result["n_folds"],
            rolling_result["avg_score"], rolling_result["n_folds"],
            best_policy,
        )

        return {
            "best_policy": best_policy,
            "expanding": expanding_result,
            "rolling": rolling_result,
            "sport": sport,
            "metric": self.metric,
        }
