"""
Multi-objective optimization with Pareto front for betting model training.

Uses Optuna to simultaneously optimize ROI, drawdown, and Sharpe ratio,
producing a Pareto front of non-dominated solutions. The user can then
pick a model that matches their risk tolerance (e.g., max Sharpe with
drawdown < 15%).

Usage:
    from src.ml.training.multi_objective import MultiObjectiveOptimizer

    optimizer = MultiObjectiveOptimizer(
        X_train, y_train, odds_train,
        X_val, y_val, odds_val,
        n_trials=100,
    )
    study = optimizer.optimize()
    best = optimizer.select_model(strategy="max_sharpe_dd_lt_15")
    model = optimizer.train_final(best.params)

CLI:
    python scripts/train_bot.py football --multi-objective --n-trials 100
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import numpy as np
import xgboost as xgb

try:
    import optuna
    from optuna.samplers import NSGAIISampler
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

from src.ml.training.clv_metrics import (
    roi_at_k,
    sharpe_ratio,
)
from src.ml.training.clv_objective import clv_xgb_objective

logger = logging.getLogger("multi_objective")


class SelectionStrategy(Enum):
    """Strategy for picking a point from the Pareto front."""
    MAX_SHARPE = "max_sharpe"
    MAX_ROI = "max_roi"
    MIN_DRAWDOWN = "min_drawdown"
    MAX_SHARPE_DD_LT_15 = "max_sharpe_dd_lt_15"  # Max Sharpe with drawdown < 15%
    MAX_SORTINO = "max_sortino"
    BALANCED = "balanced"  # Equal weight to all objectives


def _compute_drawdown(returns: np.ndarray) -> float:
    """Compute maximum drawdown from per-bet returns."""
    equity = np.cumsum(returns) + 1.0
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity) / np.where(peak > 0, peak, 1.0)
    return float(np.max(dd)) if len(dd) > 0 else 0.0


def _simulate_betting_returns(
    predictions: np.ndarray,
    labels: np.ndarray,
    odds: np.ndarray,
    min_edge: float = 0.03,
    commission_rate: float = 0.05,
) -> np.ndarray:
    """
    Simulate per-bet returns for value bets (edge > min_edge).
    Returns array of returns (profit/loss as fraction of unit stake).
    """
    implied = 1.0 / odds
    edges = predictions - implied
    bet_mask = edges > min_edge

    returns = []
    for i in range(len(predictions)):
        if bet_mask[i]:
            if labels[i] == 1:
                gross = odds[i] - 1.0
                net = gross * (1.0 - commission_rate)
                returns.append(net)
            else:
                returns.append(-1.0)
    return np.array(returns) if returns else np.array([0.0])


class MultiObjectiveOptimizer:
    """
    Optuna-based multi-objective optimizer for betting models.

    Objectives (all maximized, except drawdown which is minimized):
    1. ROI — profitability of top-k value bets
    2. Sharpe ratio — risk-adjusted returns
    3. Max drawdown — capital preservation (minimized)

    The Pareto front shows trade-offs between these objectives.
    """

    def __init__(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        odds_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        odds_val: np.ndarray,
        closing_odds_train: Optional[np.ndarray] = None,
        closing_odds_val: Optional[np.ndarray] = None,
        n_trials: int = 100,
        objective: str = "clv",
        min_edge: float = 0.03,
        commission_rate: float = 0.05,
        k_roi: int = 50,
    ):
        if not HAS_OPTUNA:
            raise ImportError(
                "optuna is required for multi-objective optimization. "
                "Install with: poetry add optuna"
            )

        self.X_train = X_train
        self.y_train = y_train
        self.odds_train = odds_train
        self.X_val = X_val
        self.y_val = y_val
        self.odds_val = odds_val
        self.closing_odds_train = closing_odds_train or odds_train
        self.closing_odds_val = closing_odds_val or odds_val
        self.n_trials = n_trials
        self.objective = objective
        self.min_edge = min_edge
        self.commission_rate = commission_rate
        self.k_roi = k_roi

        self._study: Optional[optuna.Study] = None
        self._best_params: Optional[Dict[str, Any]] = None

    def _objective(self, trial: optuna.Trial) -> Tuple[float, float, float]:
        """
        Optuna objective function. Returns (roi, sharpe, -drawdown).
        Optuna minimizes, so we negate ROI and Sharpe, and keep drawdown positive.
        """
        # Hyperparameter search space
        params = {
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "eta": trial.suggest_float("eta", 0.01, 0.3, log=True),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "lambda": trial.suggest_float("lambda", 1e-3, 10.0, log=True),
            "alpha": trial.suggest_float("alpha", 0.0, 5.0),
            "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=50),
        }

        # Train XGBoost model
        xgb_params = {
            "tree_method": "hist",
            "max_depth": params["max_depth"],
            "eta": params["eta"],
            "min_child_weight": params["min_child_weight"],
            "subsample": params["subsample"],
            "colsample_bytree": params["colsample_bytree"],
            "lambda": params["lambda"],
            "alpha": params["alpha"],
            "verbosity": 0,
        }

        if self.objective == "clv":
            dtrain = xgb.DMatrix(self.X_train, label=self.y_train)
            dval = xgb.DMatrix(self.X_val, label=self.y_val)
            dtrain.set_float_info("opening_odds", self.odds_train)
            dtrain.set_float_info("closing_odds", self.closing_odds_train)
            dval.set_float_info("opening_odds", self.odds_val)
            dval.set_float_info("closing_odds", self.closing_odds_val)

            model = xgb.train(
                params=xgb_params,
                dtrain=dtrain,
                num_boost_round=params["n_estimators"],
                obj=clv_xgb_objective,
                evals=[(dval, "val")],
                verbose_eval=False,
            )
            raw_preds = model.predict(dval)
            preds = 1.0 / (1.0 + np.exp(-raw_preds))
        else:
            clf = xgb.XGBClassifier(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                learning_rate=params["eta"],
                min_child_weight=params["min_child_weight"],
                subsample=params["subsample"],
                colsample_bytree=params["colsample_bytree"],
                reg_lambda=params["lambda"],
                reg_alpha=params["alpha"],
                eval_metric="logloss",
                verbosity=0,
            )
            clf.fit(self.X_train, self.y_train)
            preds = clf.predict_proba(self.X_val)[:, 1]

        # Compute objectives
        roi_result = roi_at_k(
            preds, self.y_val, self.odds_val,
            k=self.k_roi, commission_rate=self.commission_rate,
            min_edge=self.min_edge,
        )
        roi = roi_result["roi"]

        sim_returns = _simulate_betting_returns(
            preds, self.y_val, self.odds_val,
            min_edge=self.min_edge, commission_rate=self.commission_rate,
        )
        sharpe = sharpe_ratio(sim_returns, annualize=False)
        max_dd = _compute_drawdown(sim_returns)

        # Optuna minimizes → negate ROI and Sharpe, keep drawdown positive
        return -roi, -sharpe, max_dd

    def optimize(self) -> optuna.Study:
        """
        Run multi-objective optimization with NSGA-II sampler.
        Returns the Optuna study with the Pareto front.
        """
        sampler = NSGAIISampler(population_size=50)
        self._study = optuna.create_study(
            directions=["minimize", "minimize", "minimize"],
            sampler=sampler,
            study_name="vbq_multi_objective",
        )
        self._study.optimize(self._objective, n_trials=self.n_trials, show_progress_bar=False)

        # Log Pareto front
        pareto_trials = self._study.best_trials
        logger.info(
            "Pareto front has %d non-dominated solutions",
            len(pareto_trials),
        )
        for i, t in enumerate(pareto_trials[:5]):
            logger.info(
                "  Pareto[%d]: ROI=%.4f, Sharpe=%.4f, MaxDD=%.4f",
                i, -t.values[0], -t.values[1], t.values[2],
            )

        return self._study

    def select_model(
        self,
        strategy: SelectionStrategy = SelectionStrategy.MAX_SHARPE_DD_LT_15,
        max_drawdown: float = 0.15,
    ) -> optuna.FrozenTrial:
        """
        Select a model from the Pareto front based on the given strategy.

        Args:
            strategy: How to pick the best point from the Pareto front
            max_drawdown: Maximum acceptable drawdown (used with DD constraints)

        Returns:
            The selected Optuna trial with best hyperparameters
        """
        if self._study is None:
            raise RuntimeError("Call optimize() first")

        pareto_trials = self._study.best_trials
        if not pareto_trials:
            raise RuntimeError("No Pareto-optimal trials found")

        if strategy == SelectionStrategy.MAX_ROI:
            best = max(pareto_trials, key=lambda t: -t.values[0])
        elif strategy == SelectionStrategy.MAX_SHARPE:
            best = max(pareto_trials, key=lambda t: -t.values[1])
        elif strategy == SelectionStrategy.MIN_DRAWDOWN:
            best = min(pareto_trials, key=lambda t: t.values[2])
        elif strategy == SelectionStrategy.MAX_SHARPE_DD_LT_15:
            # Filter by drawdown constraint, then maximize Sharpe
            feasible = [t for t in pareto_trials if t.values[2] <= max_drawdown]
            if not feasible:
                logger.warning(
                    "No Pareto point with drawdown <= %.1f%%. Relaxing constraint.",
                    max_drawdown * 100,
                )
                feasible = pareto_trials
            best = max(feasible, key=lambda t: -t.values[1])
        elif strategy == SelectionStrategy.MAX_SORTINO:
            # Approximate: use Sharpe as proxy (Sortino computed on full train)
            best = max(pareto_trials, key=lambda t: -t.values[1])
        elif strategy == SelectionStrategy.BALANCED:
            # Normalize each objective to [0, 1] and minimize sum
            rois = [-t.values[0] for t in pareto_trials]
            sharpes = [-t.values[1] for t in pareto_trials]
            dds = [t.values[2] for t in pareto_trials]

            def norm(vals, higher_better=True):
                mn, mx = min(vals), max(vals)
                if mx - mn < 1e-10:
                    return [0.5] * len(vals)
                if higher_better:
                    return [(v - mn) / (mx - mn) for v in vals]
                return [(mx - v) / (mx - mn) for v in vals]

            n_roi = norm(rois, higher_better=True)
            n_sharpe = norm(sharpes, higher_better=True)
            n_dd = norm(dds, higher_better=False)

            scores = [r + s + d for r, s, d in zip(n_roi, n_sharpe, n_dd)]
            best_idx = np.argmax(scores)
            best = pareto_trials[best_idx]
        else:
            best = max(pareto_trials, key=lambda t: -t.values[1])

        logger.info(
            "Selected model (strategy=%s): ROI=%.4f, Sharpe=%.4f, MaxDD=%.4f",
            strategy.value, -best.values[0], -best.values[1], best.values[2],
        )
        self._best_params = best.params
        return best

    def train_final(self, params: Optional[Dict[str, Any]] = None) -> xgb.XGBClassifier:
        """
        Train the final model with the selected hyperparameters on full data.
        """
        if params is None:
            params = self._best_params
        if params is None:
            raise RuntimeError("No params selected. Call select_model() first.")

        logger.info("Training final model with selected params: %s", params)

        clf = xgb.XGBClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            learning_rate=params["eta"],
            min_child_weight=params["min_child_weight"],
            subsample=params["subsample"],
            colsample_bytree=params["colsample_bytree"],
            reg_lambda=params["lambda"],
            reg_alpha=params["alpha"],
            eval_metric="logloss",
            verbosity=0,
        )
        clf.fit(self.X_train, self.y_train)
        return clf

    def get_pareto_dataframe(self) -> Any:
        """Return Pareto front as a DataFrame for visualization."""
        import pandas as pd

        if self._study is None:
            raise RuntimeError("Call optimize() first")

        rows = []
        for t in self._study.best_trials:
            row = {
                "roi": -t.values[0],
                "sharpe": -t.values[1],
                "max_drawdown": t.values[2],
                **t.params,
            }
            rows.append(row)
        return pd.DataFrame(rows)
