"""
Incremental trainer with sliding window — keeps model updated without full retrain.

Instead of retraining from scratch, this trainer:
1. Removes data older than max_age_days
2. Adds new data incrementally
3. Uses XGBoost's incremental training (xgb.train with xgb_model=prev_model)
4. Validates that the updated model outperforms the old one on recent data

This keeps the model current with evolving market dynamics while being
computationally efficient.

Usage:
    from src.ml.training.incremental_trainer import IncrementalTrainer

    trainer = IncrementalTrainer(max_age_days=365, min_new_samples=50)
    result = trainer.update(prev_model, old_df, new_df)
    # result["improved"] == True → use new model
    # result["improved"] == False → keep old model
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import brier_score_loss

from src.ml.training.clv_metrics import evaluate_model_clv
from src.ml.training.clv_objective import clv_xgb_objective, time_decay_weights

logger = logging.getLogger("incremental_trainer")


class IncrementalTrainer:
    """
    Incremental/sliding-window trainer for XGBoost models.

    Maintains a rolling window of training data and incrementally
    updates the model when new data arrives. Only accepts the update
    if the new model outperforms the old one on recent validation data.
    """

    def __init__(
        self,
        max_age_days: int = 365,
        min_new_samples: int = 50,
        incremental_rounds: int = 50,
        validation_window_days: int = 30,
        improvement_threshold: float = 0.001,
        objective: str = "logloss",
        commission_rate: float = 0.05,
        min_edge: float = 0.03,
        decay_lambda: float = 0.005,
        use_time_decay: bool = True,
    ):
        """
        Args:
            max_age_days: Maximum age of training data (older is dropped)
            min_new_samples: Minimum new samples required to trigger update
            incremental_rounds: Number of boosting rounds for incremental training
            validation_window_days: Recent window for validation comparison
            improvement_threshold: Minimum metric improvement to accept new model
            objective: Training objective ("logloss" or "clv")
            commission_rate: Commission for ROI evaluation
            min_edge: Minimum edge for ROI evaluation
        """
        self.max_age_days = max_age_days
        self.min_new_samples = min_new_samples
        self.incremental_rounds = incremental_rounds
        self.validation_window_days = validation_window_days
        self.improvement_threshold = improvement_threshold
        self.objective = objective
        self.commission_rate = commission_rate
        self.min_edge = min_edge
        self.decay_lambda = decay_lambda
        self.use_time_decay = use_time_decay

        self._last_update_time: Optional[float] = None
        self._update_count: int = 0

    def _filter_by_age(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
        reference_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Remove data older than max_age_days."""
        ref = reference_date or datetime.now()
        cutoff = ref - timedelta(days=self.max_age_days)

        if not np.issubdtype(df[date_col].dtype, np.datetime64):
            df[date_col] = pd.to_datetime(df[date_col])

        filtered = df[df[date_col] >= cutoff].copy()
        removed = len(df) - len(filtered)
        if removed > 0:
            logger.info("Sliding window: removed %d samples older than %d days", removed, self.max_age_days)
        return filtered

    def _split_train_val(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split into train (all but last N days) and validation (last N days)."""
        if not np.issubdtype(df[date_col].dtype, np.datetime64):
            df[date_col] = pd.to_datetime(df[date_col])

        max_date = df[date_col].max()
        val_cutoff = max_date - timedelta(days=self.validation_window_days)

        train = df[df[date_col] < val_cutoff]
        val = df[df[date_col] >= val_cutoff]
        return train, val

    def update(
        self,
        prev_model: Any,
        old_df: pd.DataFrame,
        new_df: pd.DataFrame,
        date_col: str = "date",
        target_col: str = "actual_outcome",
        odds_col: str = "odd_1",
        closing_odds_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Incrementally update the model with new data.

        Steps:
        1. Merge old + new data
        2. Apply sliding window (remove old data)
        3. Split into train/val
        4. Train incrementally (warm start from prev_model)
        5. Compare new vs old model on validation set
        6. Accept only if improvement exceeds threshold

        Returns:
            Dict with new_model, improved, old_metrics, new_metrics
        """
        start_time = time.time()

        # Step 1: Merge data
        combined = pd.concat([old_df, new_df], ignore_index=True)
        if not np.issubdtype(combined[date_col].dtype, np.datetime64):
            combined[date_col] = pd.to_datetime(combined[date_col])
        combined = combined.sort_values(date_col).reset_index(drop=True)

        # Step 2: Apply sliding window
        reference_date = combined[date_col].max()
        filtered = self._filter_by_age(combined, date_col, reference_date)

        # Check if we have enough new data
        n_new = len(new_df)
        if n_new < self.min_new_samples:
            logger.info(
                "Only %d new samples (min %d) — skipping update",
                n_new, self.min_new_samples,
            )
            return {
                "updated": False,
                "reason": f"insufficient_new_data ({n_new} < {self.min_new_samples})",
                "new_model": prev_model,
            }

        # Step 3: Split
        train_df, val_df = self._split_train_val(filtered, date_col)

        if val_df.empty or train_df.empty:
            return {
                "updated": False,
                "reason": "insufficient_data_for_split",
                "new_model": prev_model,
            }

        # Prepare features
        feature_cols = [c for c in train_df.columns if c not in {date_col, target_col, odds_col, closing_odds_col, "game_date"}]
        X_train = train_df[feature_cols].values
        y_train = train_df[target_col].values
        X_val = val_df[feature_cols].values
        y_val = val_df[target_col].values
        odds_val = val_df[odds_col].values if odds_col in val_df.columns else np.ones(len(val_df)) * 2.0
        closing_val = val_df[closing_odds_col].values if closing_odds_col and closing_odds_col in val_df.columns else odds_val

        # Step 4: Evaluate old model on validation
        old_preds = self._predict(prev_model, X_val)
        old_metrics = self._evaluate(old_preds, y_val, odds_val, closing_val)

        # Step 5: Train incrementally
        # Apply exponential time decay weights (recent data weighted more)
        sample_weights = None
        if self.use_time_decay and date_col in train_df.columns:
            timestamps = train_df[date_col].tolist()
            sample_weights = time_decay_weights(timestamps, decay_lambda=self.decay_lambda)

        if self.objective == "clv" and odds_col in train_df.columns:
            dtrain = xgb.DMatrix(X_train, label=y_train)
            odds_train = train_df[odds_col].values
            closing_train = train_df[closing_odds_col].values if closing_odds_col and closing_odds_col in train_df.columns else odds_train
            dtrain.set_float_info("opening_odds", odds_train)
            dtrain.set_float_info("closing_odds", closing_train)

            # Get the raw model object for warm start
            if isinstance(prev_model, xgb.XGBClassifier):
                prev_booster = prev_model.get_booster()
            elif isinstance(prev_model, xgb.Booster):
                prev_booster = prev_model
            else:
                prev_booster = None

            new_booster = xgb.train(
                params={"tree_method": "hist", "max_depth": 4, "eta": 0.05, "verbosity": 0},
                dtrain=dtrain,
                num_boost_round=self.incremental_rounds,
                obj=clv_xgb_objective,
                xgb_model=prev_booster,
                verbose_eval=False,
            )
            dval = xgb.DMatrix(X_val)
            raw_preds = new_booster.predict(dval)
            new_preds = 1.0 / (1.0 + np.exp(-raw_preds))
        else:
            new_model = xgb.XGBClassifier(
                n_estimators=self.incremental_rounds,
                max_depth=4,
                learning_rate=0.05,
                eval_metric="logloss",
                verbosity=0,
            )
            # XGBClassifier supports sample_weight in fit
            fit_kwargs = {}
            if sample_weights is not None:
                fit_kwargs["sample_weight"] = sample_weights
            new_model.fit(X_train, y_train, **fit_kwargs)
            new_preds = new_model.predict_proba(X_val)[:, 1]
            new_booster = new_model

        # Step 6: Evaluate new model
        new_metrics = self._evaluate(new_preds, y_val, odds_val, closing_val)

        # Step 7: Compare
        primary_metric = "roi_top50" if "roi_top50" in new_metrics else "brier"
        old_val = old_metrics.get(primary_metric, 0)
        new_val = new_metrics.get(primary_metric, 0)

        # For Brier, lower is better; for ROI, higher is better
        if primary_metric == "brier":
            improved = (old_val - new_val) > self.improvement_threshold
        else:
            improved = (new_val - old_val) > self.improvement_threshold

        elapsed = time.time() - start_time
        self._update_count += 1
        self._last_update_time = time.time()

        result = {
            "updated": improved,
            "improved": improved,
            "old_metrics": old_metrics,
            "new_metrics": new_metrics,
            "new_model": new_booster if improved else prev_model,
            "n_train": len(train_df),
            "n_val": len(val_df),
            "n_new_samples": n_new,
            "primary_metric": primary_metric,
            "old_primary": old_val,
            "new_primary": new_val,
            "elapsed_seconds": round(elapsed, 2),
            "update_count": self._update_count,
        }

        if improved:
            logger.info(
                "Model UPDATED: %s %.4f → %.4f (train=%d, val=%d, %.1fs)",
                primary_metric, old_val, new_val, len(train_df), len(val_df), elapsed,
            )
        else:
            logger.info(
                "Model KEPT: %s %.4f → %.4f (no improvement > %.4f)",
                primary_metric, old_val, new_val, self.improvement_threshold,
            )

        return result

    def _predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Get probability predictions from a model."""
        try:
            if isinstance(model, xgb.Booster):
                dmat = xgb.DMatrix(X)
                raw = model.predict(dmat)
                return 1.0 / (1.0 + np.exp(-raw))
            elif isinstance(model, xgb.XGBClassifier):
                return model.predict_proba(X)[:, 1]
            elif hasattr(model, "predict_proba"):
                return model.predict_proba(X)[:, 1]
            else:
                return np.full(len(X), 0.5)
        except Exception as e:
            logger.warning("Prediction failed: %s", e)
            return np.full(len(X), 0.5)

    def _evaluate(
        self,
        preds: np.ndarray,
        y: np.ndarray,
        odds: np.ndarray,
        closing_odds: np.ndarray,
    ) -> Dict[str, float]:
        """Evaluate predictions with comprehensive metrics."""
        try:
            if np.std(closing_odds) > 1e-8 and np.std(odds) > 1e-8:
                return evaluate_model_clv(
                    preds, y, odds, closing_odds,
                    commission_rate=self.commission_rate,
                    min_edge=self.min_edge,
                )
        except Exception:
            pass

        # Fallback to basic metrics
        return {
            "brier": round(brier_score_loss(y, preds), 6),
            "mean_prob": round(float(np.mean(preds)), 4),
        }

    @property
    def status(self) -> Dict[str, Any]:
        """Get current trainer status."""
        return {
            "max_age_days": self.max_age_days,
            "min_new_samples": self.min_new_samples,
            "incremental_rounds": self.incremental_rounds,
            "update_count": self._update_count,
            "last_update": self._last_update_time,
        }
