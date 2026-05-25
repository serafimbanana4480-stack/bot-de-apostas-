"""
Nested cross-validation for robust hyperparameter optimization.

Problem: Walk-forward validates the model, but hyperparameters are either
fixed or optimized on the same data used for training → overfitting.

Solution: For each outer fold (walk-forward), run an inner optimization
(grid or bayesian) on the training split only. The inner CV selects the
best hyperparameters, and the outer fold evaluates generalization.

This gives an unbiased estimate of model performance with tuned hyperparameters.

Usage:
    from src.ml.training.nested_cv import NestedWalkForwardCV

    nested = NestedWalkForwardCV(
        n_outer=5,
        n_inner=3,
        optimizer="bayesian",  # or "grid"
        n_trials=30,
    )
    result = nested.fit(X, y, odds, date_col="game_date")
    # result contains outer-fold metrics with tuned hyperparameters
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

from src.ml.training.clv_metrics import evaluate_model_clv
from src.ml.training.clv_objective import clv_xgb_objective
from src.validation.splits import PurgedWalkForwardCV

logger = logging.getLogger("nested_cv")


# Default hyperparameter grid for grid search
DEFAULT_PARAM_GRID = {
    "max_depth": [3, 4, 5, 6],
    "eta": [0.01, 0.05, 0.1, 0.2],
    "min_child_weight": [1, 5, 10, 20],
    "subsample": [0.6, 0.8, 1.0],
    "colsample_bytree": [0.6, 0.8, 1.0],
    "n_estimators": [50, 100, 200],
}


class NestedWalkForwardCV:
    """
    Nested walk-forward cross-validation with inner hyperparameter optimization.

    Outer loop: Walk-forward splits (temporal, purged)
    Inner loop: Hyperparameter optimization on each outer training split

    This prevents overfitting hyperparameters to the validation data.
    """

    def __init__(
        self,
        n_outer: int = 5,
        n_inner: int = 3,
        optimizer: str = "bayesian",
        n_trials: int = 30,
        param_grid: Optional[Dict[str, list]] = None,
        objective: str = "logloss",
        embargo_days: int = 7,
        min_edge: float = 0.03,
        commission_rate: float = 0.05,
    ):
        """
        Args:
            n_outer: Number of outer walk-forward folds
            n_inner: Number of inner CV folds for hyperparameter tuning
            optimizer: "bayesian" (Optuna) or "grid" (exhaustive)
            n_trials: Number of Optuna trials (only for bayesian)
            param_grid: Custom parameter grid (only for grid search)
            objective: Training objective ("logloss" or "clv")
            embargo_days: Purge gap between train and test
            min_edge: Minimum edge for ROI evaluation
            commission_rate: Commission for ROI calculation
        """
        self.n_outer = n_outer
        self.n_inner = n_inner
        self.optimizer = optimizer
        self.n_trials = n_trials
        self.param_grid = param_grid or DEFAULT_PARAM_GRID
        self.objective = objective
        self.embargo_days = embargo_days
        self.min_edge = min_edge
        self.commission_rate = commission_rate

    def _inner_optimize_bayesian(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        odds_train: np.ndarray,
    ) -> Dict[str, Any]:
        """Run Optuna bayesian optimization on the inner training split."""
        if not HAS_OPTUNA:
            logger.warning("Optuna not available, falling back to grid search")
            return self._inner_optimize_grid(X_train, y_train, odds_train)

        def inner_objective(trial: optuna.Trial) -> float:
            params = {
                "max_depth": trial.suggest_int("max_depth", 2, 8),
                "eta": trial.suggest_float("eta", 0.01, 0.3, log=True),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=50),
            }

            # Inner walk-forward CV
            inner_cv = PurgedWalkForwardCV(n_splits=self.n_inner)
            X_df = pd.DataFrame(X_train)
            inner_splits = list(inner_cv.split(X_df))

            inner_scores = []
            for train_idx, val_idx in inner_splits:
                X_it, y_it = X_train[train_idx], y_train[train_idx]
                X_iv, y_iv = X_train[val_idx], y_train[val_idx]
                odds_iv = odds_train[val_idx]

                clf = xgb.XGBClassifier(
                    n_estimators=params["n_estimators"],
                    max_depth=params["max_depth"],
                    learning_rate=params["eta"],
                    min_child_weight=params["min_child_weight"],
                    subsample=params["subsample"],
                    colsample_bytree=params["colsample_bytree"],
                    eval_metric="logloss",
                    verbosity=0,
                )
                clf.fit(X_it, y_it)
                preds = clf.predict_proba(X_iv)[:, 1]

                # Evaluate with Brier score (lower is better)
                score = brier_score_loss(y_iv, preds)
                inner_scores.append(score)

            return np.mean(inner_scores)

        study = optuna.create_study(direction="minimize")
        study.optimize(inner_objective, n_trials=self.n_trials, show_progress_bar=False)

        best = study.best_params
        best["n_estimators"] = best.get("n_estimators", 100)
        return best

    def _inner_optimize_grid(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        odds_train: np.ndarray,
    ) -> Dict[str, Any]:
        """Run grid search on the inner training split."""
        from itertools import product

        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        best_score = float("inf")
        best_params = {}

        for combo in product(*values):
            params = dict(zip(keys, combo))

            inner_cv = PurgedWalkForwardCV(n_splits=self.n_inner)
            X_df = pd.DataFrame(X_train)
            inner_splits = list(inner_cv.split(X_df))

            inner_scores = []
            for train_idx, val_idx in inner_splits:
                X_it, y_it = X_train[train_idx], y_train[train_idx]
                X_iv, y_iv = X_train[val_idx], y_train[val_idx]

                clf = xgb.XGBClassifier(
                    n_estimators=params.get("n_estimators", 100),
                    max_depth=params.get("max_depth", 4),
                    learning_rate=params.get("eta", 0.05),
                    min_child_weight=params.get("min_child_weight", 1),
                    subsample=params.get("subsample", 0.8),
                    colsample_bytree=params.get("colsample_bytree", 0.8),
                    eval_metric="logloss",
                    verbosity=0,
                )
                clf.fit(X_it, y_it)
                preds = clf.predict_proba(X_iv)[:, 1]
                score = brier_score_loss(y_iv, preds)
                inner_scores.append(score)

            avg_score = np.mean(inner_scores)
            if avg_score < best_score:
                best_score = avg_score
                best_params = params

        return best_params

    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        odds: np.ndarray,
        date_col: str = "game_date",
        closing_odds: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Run nested walk-forward cross-validation.

        Args:
            X: Feature DataFrame (must include date_col for temporal splits)
            y: Target array
            odds: Opening odds array
            date_col: Name of date column in X
            closing_odds: Closing odds array (for CLV evaluation)

        Returns:
            Dict with outer-fold metrics, best params per fold, and overall results
        """
        outer_cv = PurgedWalkForwardCV(n_splits=self.n_outer)
        outer_splits = list(outer_cv.split(X))

        feature_cols = [c for c in X.columns if c != date_col]
        oof_preds = np.zeros(len(X))
        fold_results = []
        all_best_params = []

        for fold_idx, (train_idx, val_idx) in enumerate(outer_splits):
            logger.info("Nested CV — Outer fold %d/%d", fold_idx + 1, self.n_outer)

            X_train = X.iloc[train_idx][feature_cols].values
            y_train = y[train_idx]
            odds_train = odds[train_idx]
            X_val = X.iloc[val_idx][feature_cols].values
            y_val = y[val_idx]
            odds_val = odds[val_idx]
            closing_val = closing_odds[val_idx] if closing_odds is not None else odds_val

            # --- Inner loop: hyperparameter optimization ---
            logger.info("  Running inner optimization (%s)...", self.optimizer)
            if self.optimizer == "bayesian":
                best_params = self._inner_optimize_bayesian(X_train, y_train, odds_train)
            else:
                best_params = self._inner_optimize_grid(X_train, y_train, odds_train)

            all_best_params.append(best_params)
            logger.info("  Best params for fold %d: %s", fold_idx + 1, best_params)

            # --- Outer evaluation with tuned hyperparameters ---
            if self.objective == "clv" and closing_odds is not None:
                dtrain = xgb.DMatrix(X_train, label=y_train)
                dval = xgb.DMatrix(X_val, label=y_val)
                dtrain.set_float_info("opening_odds", odds_train)
                dtrain.set_float_info("closing_odds", closing_odds[train_idx] if closing_odds is not None else odds_train)
                dval.set_float_info("opening_odds", odds_val)
                dval.set_float_info("closing_odds", closing_val)

                model = xgb.train(
                    params={
                        "tree_method": "hist",
                        "max_depth": best_params.get("max_depth", 4),
                        "eta": best_params.get("eta", 0.05),
                        "verbosity": 0,
                    },
                    dtrain=dtrain,
                    num_boost_round=best_params.get("n_estimators", 100),
                    obj=clv_xgb_objective,
                    evals=[(dval, "val")],
                    verbose_eval=False,
                )
                raw_preds = model.predict(dval)
                preds = 1.0 / (1.0 + np.exp(-raw_preds))
            else:
                clf = xgb.XGBClassifier(
                    n_estimators=best_params.get("n_estimators", 100),
                    max_depth=best_params.get("max_depth", 4),
                    learning_rate=best_params.get("eta", 0.05),
                    min_child_weight=best_params.get("min_child_weight", 1),
                    subsample=best_params.get("subsample", 0.8),
                    colsample_bytree=best_params.get("colsample_bytree", 0.8),
                    eval_metric="logloss",
                    verbosity=0,
                )
                clf.fit(X_train, y_train)
                preds = clf.predict_proba(X_val)[:, 1]

            oof_preds[val_idx] = preds

            # Evaluate outer fold
            if closing_odds is not None:
                clv_metrics = evaluate_model_clv(
                    preds, y_val, odds_val, closing_val,
                    commission_rate=self.commission_rate,
                    min_edge=self.min_edge,
                )
            else:
                clv_metrics = {
                    "brier": brier_score_loss(y_val, preds),
                    "auc": roc_auc_score(y_val, preds) if len(np.unique(y_val)) > 1 else 0.0,
                }

            fold_results.append({
                "fold": fold_idx + 1,
                "best_params": best_params,
                "metrics": clv_metrics,
            })
            logger.info("  Fold %d metrics: %s", fold_idx + 1, clv_metrics)

        # Overall OOF evaluation
        if closing_odds is not None:
            overall_metrics = evaluate_model_clv(
                oof_preds, y, odds, closing_odds,
                commission_rate=self.commission_rate,
                min_edge=self.min_edge,
            )
        else:
            overall_metrics = {
                "brier": brier_score_loss(y, oof_preds),
                "auc": roc_auc_score(y, oof_preds) if len(np.unique(y)) > 1 else 0.0,
            }

        # Calibrate OOF predictions
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrator.fit(oof_preds, y)

        return {
            "overall_metrics": overall_metrics,
            "fold_results": fold_results,
            "best_params_per_fold": all_best_params,
            "oof_predictions": oof_preds,
            "calibrator": calibrator,
            "n_outer_folds": self.n_outer,
            "optimizer": self.optimizer,
        }
