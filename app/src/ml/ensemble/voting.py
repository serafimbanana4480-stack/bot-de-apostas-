"""
Voting ensemble — soft voting with CLV-adjusted dynamic weights.

Simpler than stacking, but more robust with small datasets.
Weights are updated every 30 days based on recent CLV performance.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]

from src.ml.ensemble.base import ArrayLike, EnsembleModel, _get_column, _to_numpy

logger = logging.getLogger("voting_ensemble")


class VotingEnsemble(EnsembleModel):
    """
    Soft voting ensemble with dynamic CLV-adjusted weights.

    Each model votes with its predicted probability, and votes are
    weighted by the model's recent CLV performance. Models that
    consistently beat the closing line get more weight.
    """

    def __init__(
        self,
        clv_weight_decay: float = 0.95,
        min_weight: float = 0.05,
        reweight_interval_days: int = 30,
    ):
        self.clv_weight_decay = clv_weight_decay
        self.min_weight = min_weight
        self.reweight_interval_days = reweight_interval_days

        self.level0_models: dict[str, Any] = {}
        self._model_names: list[str] = []
        self._weights: dict[str, float] = {}
        self._last_reweight_date: str | None = None

    def fit(
        self,
        X_train: ArrayLike,
        y_train: np.ndarray,
        opening_odds: np.ndarray | None = None,
        closing_odds: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Train all Level-0 models with equal initial weights."""
        import xgboost as xgb
        from sklearn.linear_model import LogisticRegression as LR

        X_arr = _to_numpy(X_train)
        self._model_names = ["xgboost", "logistic", "baseline"]

        # --- XGBoost ---
        try:
            xgb_model = xgb.XGBClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.05,
                eval_metric="logloss", random_state=42,
            )
            xgb_model.fit(X_arr, y_train)
            self.level0_models["xgboost"] = xgb_model
        except Exception as e:
            logger.warning("XGBoost training failed: %s", e)

        # --- Logistic Regression ---
        try:
            lr_model = LR(max_iter=500, random_state=42)
            lr_model.fit(X_arr, y_train)
            self.level0_models["logistic"] = lr_model
        except Exception as e:
            logger.warning("Logistic training failed: %s", e)

        # Initialize equal weights
        n_active = len(self.level0_models) + 1  # +1 for baseline
        self._weights = {name: 1.0 / n_active for name in self._model_names}

        return {
            "n_models": len(self._model_names),
            "initial_weights": dict(self._weights),
            "model_names": self._model_names,
        }

    def predict(self, X: ArrayLike) -> np.ndarray:
        """Generate weighted average predictions."""
        preds = self._get_level0_predictions(X)

        X_arr = _to_numpy(X)
        weights = np.array([self._weights.get(name, 0.33) for name in self._model_names])
        weights = weights / weights.sum()  # Normalize

        weighted_sum = np.zeros(len(X_arr))
        for w, name in zip(weights, self._model_names):
            if name in preds:
                weighted_sum += w * preds[name]

        return weighted_sum

    def _get_level0_predictions(self, X: ArrayLike) -> dict[str, np.ndarray]:
        """Get predictions from all Level-0 models."""
        X_arr = _to_numpy(X)
        preds = {}

        if "xgboost" in self.level0_models:
            try:
                preds["xgboost"] = self.level0_models["xgboost"].predict_proba(X_arr)[:, 1]
            except Exception:
                preds["xgboost"] = np.full(len(X_arr), 0.5)
        else:
            preds["xgboost"] = np.full(len(X_arr), 0.5)

        if "logistic" in self.level0_models:
            try:
                preds["logistic"] = self.level0_models["logistic"].predict_proba(X_arr)[:, 1]
            except Exception:
                preds["logistic"] = np.full(len(X_arr), 0.5)
        else:
            preds["logistic"] = np.full(len(X_arr), 0.5)

        # Baseline: market implied probability
        odds_col = _get_column(X, "odds_home")
        if odds_col is not None:
            preds["baseline"] = np.where(odds_col > 1.0, 1.0 / odds_col, 0.5)
        else:
            preds["baseline"] = np.full(len(X_arr), 0.5)

        return preds

    def get_model_weights(self) -> dict[str, float]:
        """Return current voting weights."""
        return dict(self._weights)

    def update_clv_weights(self, clv_per_model: dict[str, float]) -> None:
        """
        Update voting weights based on recent CLV performance.

        Models with positive CLV get increased weight,
        models with negative CLV get decreased weight.
        Minimum weight is enforced to prevent any model from being ignored.
        """
        for name, clv in clv_per_model.items():
            if name in self._weights:
                old_weight = self._weights[name]
                adjustment = clv * self.clv_weight_decay
                new_weight = max(self.min_weight, old_weight + adjustment)
                self._weights[name] = new_weight

        # Normalize weights to sum to 1
        total = sum(self._weights.values())
        if total > 0:
            for name in self._weights:
                self._weights[name] /= total

        logger.info("Voting weights updated: %s", {k: round(v, 3) for k, v in self._weights.items()})
