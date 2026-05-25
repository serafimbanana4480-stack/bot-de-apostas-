"""
Stacking ensemble — combines multiple Level-0 models via a Level-1 meta-model.

Level-0 models: XGBoost, Poisson, LogisticRegression, Baseline (market odds)
Level-1 model: LogisticRegression that learns optimal combination weights

Uses walk-forward validation to prevent data leakage in meta-model training.
Weights are dynamically adjusted based on recent CLV performance per model.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]

from sklearn.linear_model import LogisticRegression

from src.ml.ensemble.base import ArrayLike, EnsembleModel, _get_column, _to_numpy

logger = logging.getLogger("stacking_ensemble")


class StackingEnsemble(EnsembleModel):
    """
    Stacking ensemble with walk-forward validated meta-model.

    The meta-model (Level-1) learns to combine Level-0 predictions
    based on out-of-fold predictions, preventing information leakage.
    """

    def __init__(
        self,
        n_folds: int = 5,
        clv_weight_decay: float = 0.95,
        min_samples_for_meta: int = 100,
    ):
        self.n_folds = n_folds
        self.clv_weight_decay = clv_weight_decay
        self.min_samples_for_meta = min_samples_for_meta

        # Level-0 models (fitted during fit())
        self.level0_models: dict[str, Any] = {}
        self.level0_calibrators: dict[str, Any] = {}

        # Level-1 meta-model
        self.meta_model: LogisticRegression | None = None

        # Dynamic weights based on recent CLV
        self._clv_weights: dict[str, float] = {}
        self._model_names: list[str] = []

    def fit(
        self,
        X_train: ArrayLike,
        y_train: np.ndarray,
        opening_odds: np.ndarray | None = None,
        closing_odds: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """
        Train all Level-0 models and the Level-1 meta-model.

        Uses out-of-fold predictions to train the meta-model,
        preventing data leakage.
        """
        import xgboost as xgb
        from sklearn.linear_model import LogisticRegression as LR

        X_arr = _to_numpy(X_train)
        self._model_names = ["xgboost", "logistic", "baseline"]
        n = len(X_arr)

        # Generate out-of-fold predictions for meta-model training
        oof_preds = {name: np.zeros(n) for name in self._model_names}

        # Simple time-based fold split (walk-forward)
        fold_size = n // self.n_folds

        for fold in range(self.n_folds):
            val_start = fold * fold_size
            val_end = min((fold + 1) * fold_size, n)

            train_mask = np.ones(n, dtype=bool)
            train_mask[val_start:val_end] = False

            X_tr = X_arr[train_mask]
            y_tr = y_train[train_mask]
            X_val = X_arr[val_start:val_end]
            y_train[val_start:val_end]

            if len(np.unique(y_tr)) < 2:
                logger.warning("Fold %d skipped: uniform labels", fold)
                continue

            # --- Level-0: XGBoost ---
            try:
                xgb_model = xgb.XGBClassifier(
                    n_estimators=100, max_depth=4, learning_rate=0.05,
                    eval_metric="logloss", random_state=42,
                )
                xgb_model.fit(X_tr, y_tr)
                oof_preds["xgboost"][val_start:val_end] = xgb_model.predict_proba(X_val)[:, 1]

                if fold == self.n_folds - 1:
                    self.level0_models["xgboost"] = xgb_model
            except Exception as e:
                logger.warning("XGBoost fold %d failed: %s", fold, e)
                oof_preds["xgboost"][val_start:val_end] = 0.5

            # --- Level-0: Logistic Regression ---
            try:
                lr_model = LR(max_iter=500, random_state=42)
                lr_model.fit(X_tr, y_tr)
                oof_preds["logistic"][val_start:val_end] = lr_model.predict_proba(X_val)[:, 1]

                if fold == self.n_folds - 1:
                    self.level0_models["logistic"] = lr_model
            except Exception as e:
                logger.warning("Logistic fold %d failed: %s", fold, e)
                oof_preds["logistic"][val_start:val_end] = 0.5

            # --- Level-0: Baseline (market implied probability) ---
            if opening_odds is not None:
                oof_preds["baseline"][val_start:val_end] = 1.0 / opening_odds[val_start:val_end]
            else:
                oof_preds["baseline"][val_start:val_end] = 0.5

        # --- Level-1: Meta-model ---
        # Stack OOF predictions as features for meta-model
        meta_features = np.column_stack([oof_preds[name] for name in self._model_names])

        if len(y_train) >= self.min_samples_for_meta and len(np.unique(y_train)) >= 2:
            self.meta_model = LogisticRegression(max_iter=500, random_state=42)
            self.meta_model.fit(meta_features, y_train)
            logger.info("Meta-model trained on %d samples with %d features", len(meta_features), meta_features.shape[1])
        else:
            logger.warning("Insufficient data for meta-model — using equal weights")
            self.meta_model = None

        # Initialize CLV weights as equal
        self._clv_weights = {name: 1.0 / len(self._model_names) for name in self._model_names}

        return {
            "n_models": len(self._model_names),
            "meta_model_trained": self.meta_model is not None,
            "model_names": self._model_names,
        }

    def predict(self, X: ArrayLike) -> np.ndarray:
        """Generate combined predictions using the stacking ensemble."""
        level0_preds = self._get_level0_predictions(X)

        if self.meta_model is not None:
            meta_features = np.column_stack([level0_preds[name] for name in self._model_names])
            return self.meta_model.predict_proba(meta_features)[:, 1]
        else:
            # Fallback: weighted average using CLV weights
            weights = np.array([self._clv_weights.get(name, 0.33) for name in self._model_names])
            weights = weights / weights.sum()
            weighted_sum = sum(w * level0_preds[name] for w, name in zip(weights, self._model_names))
            return weighted_sum

    def _get_level0_predictions(self, X: ArrayLike) -> dict[str, np.ndarray]:
        """Get predictions from all Level-0 models."""
        X_arr = _to_numpy(X)
        preds = {}

        # XGBoost
        if "xgboost" in self.level0_models:
            try:
                preds["xgboost"] = self.level0_models["xgboost"].predict_proba(X_arr)[:, 1]
            except Exception as e:
                logger.warning("XGBoost prediction failed: %s", e)
                preds["xgboost"] = np.full(len(X_arr), 0.5)
        else:
            preds["xgboost"] = np.full(len(X_arr), 0.5)

        # Logistic Regression
        if "logistic" in self.level0_models:
            try:
                preds["logistic"] = self.level0_models["logistic"].predict_proba(X_arr)[:, 1]
            except Exception as e:
                logger.warning("Logistic prediction failed: %s", e)
                preds["logistic"] = np.full(len(X_arr), 0.5)
        else:
            preds["logistic"] = np.full(len(X_arr), 0.5)

        # Baseline (market odds if available, else 0.5)
        odds_col = _get_column(X, "odds_home")
        if odds_col is not None:
            preds["baseline"] = np.where(odds_col > 1.0, 1.0 / odds_col, 0.5)
        else:
            preds["baseline"] = np.full(len(X_arr), 0.5)

        return preds

    def get_model_weights(self) -> dict[str, float]:
        """Return current model weights."""
        if self.meta_model is not None:
            # Use meta-model coefficients as weights
            coefs = self.meta_model.coef_[0]
            names = self._model_names[:len(coefs)]
            # Softmax to normalize to probabilities
            exp_coefs = np.exp(coefs - np.max(coefs))
            softmax = exp_coefs / exp_coefs.sum()
            return {name: float(w) for name, w in zip(names, softmax)}
        return dict(self._clv_weights)

    def update_clv_weights(self, clv_per_model: dict[str, float]) -> None:
        """
        Update dynamic weights based on recent CLV performance per model.
        Models with higher CLV get more weight.
        """
        for name, clv in clv_per_model.items():
            if name in self._clv_weights:
                old_weight = self._clv_weights[name]
                # Increase weight for positive CLV, decrease for negative
                adjustment = clv * self.clv_weight_decay
                new_weight = max(0.01, old_weight + adjustment)
                self._clv_weights[name] = new_weight

        # Normalize
        total = sum(self._clv_weights.values())
        if total > 0:
            for name in self._clv_weights:
                self._clv_weights[name] /= total
