"""
Football Hybrid Model — Poisson baseline + XGBoost second stage.

Architecture:
1. FootballPoissonModel generates structural features (expected goals, probs)
2. XGBoost learns residual patterns (form, head-to-head, market context)
3. Final prediction = calibrated blend of Poisson + XGBoost
4. Supports warm-start incremental training via xgb.train(xgb_model=prev)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression

from src.ml.models.football_poisson import FootballPoissonModel
from src.ml.serialization import isotonic_from_dict, isotonic_to_dict
from src.validation.splits import temporal_oof_split

logger = logging.getLogger(__name__)


class FootballHybridModel:
    """
    Hybrid model combining Poisson structural model with XGBoost residual learner.

    The Poisson model captures long-term team strength (attack/defense).
    The XGBoost captures short-term patterns (form, head-to-head, market context).
    Together they produce sharper predictions than either model alone.

    Incremental training:
    - Poisson component updated via EMA (FootballPoissonModel.update)
    - XGBoost updated via warm-start (xgb.train with xgb_model=prev_booster)
    """

    def __init__(
        self,
        poisson: Optional[FootballPoissonModel] = None,
        xgb_params: Optional[Dict[str, Any]] = None,
        blend_weight: float = 0.5,  # 0=Poisson only, 1=XGB only
        use_calibration: bool = True,
    ):
        self.poisson = poisson or FootballPoissonModel(use_dixon_coles=True)
        self.xgb_params = xgb_params or {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "n_estimators": 100,
            "reg_lambda": 1.0,
            "reg_alpha": 0.5,
            "min_child_weight": 10,
            "tree_method": "hist",
        }
        self.blend_weight = blend_weight
        self.use_calibration = use_calibration

        self.xgb_model: Optional[xgb.Booster] = None
        self.calibrator = IsotonicRegression(out_of_bounds="clip")
        self.is_calibrated = False

        # Training history for incremental updates
        self._feature_names: Optional[List[str]] = None
        self._training_count = 0

    def _build_features(
        self, df: pd.DataFrame, fit_poisson: bool = False
    ) -> pd.DataFrame:
        """Generate hybrid features from Poisson model + raw data."""
        if fit_poisson:
            self.poisson.fit(df, calibrate=False)

        rows = []
        for _, row in df.iterrows():
            probs = self.poisson.predict_match_outcome(
                row["home_team"],
                row["away_team"],
                league=row.get("league", row.get("competition", None)),
                apply_calibration=False,
            )
            feat = {
                # Poisson structural features
                "poisson_p1": probs["1"],
                "poisson_pX": probs["X"],
                "poisson_p2": probs["2"],
                "exp_goals_home": probs["expected_goals_home"],
                "exp_goals_away": probs["expected_goals_away"],
                "goal_diff_exp": probs["expected_goals_home"] - probs["expected_goals_away"],
                # Market features
                "odd_1": row.get("odd_1", 2.0),
                "odd_X": row.get("odd_X", 3.0),
                "odd_2": row.get("odd_2", 3.0),
                "open_odd_home": row.get("open_odd_home", row.get("odd_1", 2.0)),
                "pin_close_home": row.get("pin_close_home", row.get("odd_1", 2.0)),
                # Temporal / contextual
                "month": pd.to_datetime(row["date"]).month if "date" in row else 1,
                "is_weekend": pd.to_datetime(row["date"]).weekday() >= 5 if "date" in row else 0,
                # Derived
                "implied_prob_1": 1.0 / max(row.get("odd_1", 2.0), 1.01),
                "odds_spread": abs(row.get("odd_1", 2.0) - row.get("odd_2", 3.0)),
            }
            rows.append(feat)

        return pd.DataFrame(rows)

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "actual_outcome",
        calibration: bool = True,
    ) -> Dict[str, Any]:
        """Fit hybrid model from scratch."""
        logger.info("Fitting hybrid model on %d matches...", len(df))

        # 1. Fit Poisson
        self.poisson.fit(df, calibrate=False)

        # 2. Build features
        X = self._build_features(df, fit_poisson=False)
        self._feature_names = list(X.columns)

        y = (df[target_col].astype(str) == "1").astype(int).values if target_col in df.columns else np.ones(len(df))

        # 3. Train XGBoost
        dtrain = xgb.DMatrix(X.values, label=y, feature_names=self._feature_names)
        self.xgb_model = xgb.train(
            {k: v for k, v in self.xgb_params.items() if k != "n_estimators"},
            dtrain,
            num_boost_round=self.xgb_params.get("n_estimators", 100),
        )

        # 4. Calibrate
        if calibration and len(df) >= 30:
            self._calibrate(df, X.values, y)

        self._training_count += len(df)
        return {
            "trained": True,
            "matches": len(df),
            "features": len(self._feature_names),
        }

    def update(
        self,
        df_new: pd.DataFrame,
        alpha: Optional[float] = None,
        xgb_incremental_rounds: int = 30,
        calibration: bool = True,
        ewc_lambda: float = 0.0,
        df_old_buffer: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Incrementally update the hybrid model.

        1. Update Poisson via EMA
        2. Build features for new data (using updated Poisson)
        3. Warm-start XGBoost with new data
        4. Optionally recalibrate

        Args:
            ewc_lambda: Elastic Weight Consolidation strength.
                        0 = no EWC (standard warm-start)
                        >0 = mix old buffer with new data to prevent forgetting
            df_old_buffer: Historical data buffer for EWC distillation.
                           If provided and ewc_lambda > 0, these samples are
                           mixed with new data with weight proportional to ewc_lambda.
        """
        if df_new.empty:
            return {"updated": False, "reason": "empty_data"}

        n_new = len(df_new)

        # 1. Update Poisson component
        poisson_stats = self.poisson.update(df_new, alpha=alpha, calibrate=False)

        # 2. Build features for new data
        X_new = self._build_features(df_new, fit_poisson=False)
        if self._feature_names is None:
            self._feature_names = list(X_new.columns)
        else:
            for col in self._feature_names:
                if col not in X_new.columns:
                    X_new[col] = 0.0
            X_new = X_new[self._feature_names]

        y_new = (df_new["actual_outcome"].astype(str) == "1").astype(int).values if "actual_outcome" in df_new.columns else np.ones(n_new)

        # 3. Warm-start XGBoost
        if self.xgb_model is not None:
            # EWC: mix new data with old buffer to prevent forgetting
            if ewc_lambda > 0 and df_old_buffer is not None and len(df_old_buffer) > 0:
                n_old_ewc = min(int(n_new * ewc_lambda), len(df_old_buffer))
                old_sample = df_old_buffer.sample(n=n_old_ewc, random_state=42) if len(df_old_buffer) > n_old_ewc else df_old_buffer
                X_old = self._build_features(old_sample, fit_poisson=False)
                for col in self._feature_names:
                    if col not in X_old.columns:
                        X_old[col] = 0.0
                X_old = X_old[self._feature_names]
                y_old = (old_sample["actual_outcome"].astype(str) == "1").astype(int).values if "actual_outcome" in old_sample.columns else np.ones(len(old_sample))

                # Combine
                X_combined = pd.concat([X_new, X_old], ignore_index=True)
                y_combined = np.concatenate([y_new, y_old])
                weights = np.concatenate([
                    np.ones(n_new),  # New data weight = 1
                    np.full(n_old_ewc, ewc_lambda),  # Old data weight = lambda
                ])
                dtrain = xgb.DMatrix(X_combined.values, label=y_combined, feature_names=self._feature_names, weight=weights)
            else:
                dtrain = xgb.DMatrix(X_new.values, label=y_new, feature_names=self._feature_names)

            self.xgb_model = xgb.train(
                {k: v for k, v in self.xgb_params.items() if k != "n_estimators"},
                dtrain,
                num_boost_round=xgb_incremental_rounds,
                xgb_model=self.xgb_model,
            )
        else:
            dnew = xgb.DMatrix(X_new.values, label=y_new, feature_names=self._feature_names)
            self.xgb_model = xgb.train(
                {k: v for k, v in self.xgb_params.items() if k != "n_estimators"},
                dnew,
                num_boost_round=self.xgb_params.get("n_estimators", 100),
            )

        # 4. Recalibrate if enough data
        if calibration and n_new >= 30:
            self._calibrate(df_new, X_new.values, y_new)

        self._training_count += n_new
        return {
            "updated": True,
            "poisson_alpha": poisson_stats.get("alpha_used"),
            "xgb_rounds": xgb_incremental_rounds,
            "matches_added": n_new,
            "total_matches": self._training_count,
            "ewc_lambda": ewc_lambda,
        }

    def predict(
        self,
        home_team: str,
        away_team: str,
        odd_1: float = 2.0,
        odd_X: float = 3.0,
        odd_2: float = 3.0,
        league: Optional[str] = None,
        apply_calibration: bool = True,
        **kwargs,
    ) -> Dict[str, float]:
        """Predict match outcome probabilities."""
        # Poisson prediction
        poisson_probs = self.poisson.predict_match_outcome(
            home_team, away_team, league=league, apply_calibration=False
        )

        # Build XGBoost feature vector
        feat = {
            "poisson_p1": poisson_probs["1"],
            "poisson_pX": poisson_probs["X"],
            "poisson_p2": poisson_probs["2"],
            "exp_goals_home": poisson_probs["expected_goals_home"],
            "exp_goals_away": poisson_probs["expected_goals_away"],
            "goal_diff_exp": poisson_probs["expected_goals_home"] - poisson_probs["expected_goals_away"],
            "odd_1": odd_1,
            "odd_X": odd_X,
            "odd_2": odd_2,
            "open_odd_home": kwargs.get("open_odd_home", odd_1),
            "pin_close_home": kwargs.get("pin_close_home", odd_1),
            "month": kwargs.get("month", 1),
            "is_weekend": kwargs.get("is_weekend", 0),
            "implied_prob_1": 1.0 / max(odd_1, 1.01),
            "odds_spread": abs(odd_1 - odd_2),
        }

        if self._feature_names is None:
            # Model not trained — return Poisson only
            return poisson_probs

        # Align features
        X_pred = np.zeros((1, len(self._feature_names)))
        for i, col in enumerate(self._feature_names):
            X_pred[0, i] = feat.get(col, 0.0)

        dtest = xgb.DMatrix(X_pred, feature_names=self._feature_names)
        xgb_prob = self.xgb_model.predict(dtest)[0] if self.xgb_model else poisson_probs["1"]

        # Blend Poisson and XGBoost
        blended_p1 = (1 - self.blend_weight) * poisson_probs["1"] + self.blend_weight * xgb_prob

        # Normalize: preserve relative ratios of X and 2 from Poisson
        total_poisson_non1 = poisson_probs["X"] + poisson_probs["2"]
        if total_poisson_non1 > 0:
            blended_pX = (1 - blended_p1) * (poisson_probs["X"] / total_poisson_non1)
            blended_p2 = (1 - blended_p1) * (poisson_probs["2"] / total_poisson_non1)
        else:
            blended_pX = (1 - blended_p1) / 2
            blended_p2 = (1 - blended_p1) / 2

        probs = {"1": blended_p1, "X": blended_pX, "2": blended_p2}

        # Apply isotonic calibration
        if apply_calibration and self.is_calibrated:
            p1_cal = float(self.calibrator.transform([probs["1"]])[0])
            # Renormalize
            scale = p1_cal / probs["1"] if probs["1"] > 0 else 1.0
            probs = {
                "1": p1_cal,
                "X": min(probs["X"] * scale, 1.0 - p1_cal) if scale < 1.0 else probs["X"],
                "2": 1.0 - p1_cal - min(probs["X"] * scale, 1.0 - p1_cal) if scale < 1.0 else 1.0 - p1_cal - probs["X"],
            }

        return {
            "1": probs["1"],
            "X": probs["X"],
            "2": probs["2"],
            "expected_goals_home": poisson_probs["expected_goals_home"],
            "expected_goals_away": poisson_probs["expected_goals_away"],
            "poisson_p1": poisson_probs["1"],
            "xgb_p1": xgb_prob,
        }

    def _calibrate(self, df: pd.DataFrame, X: np.ndarray, y: np.ndarray):
        """Fit isotonic calibrator out-of-fold using temporal splits."""
        oof_preds = np.zeros(len(df))
        oof_splits = temporal_oof_split(
            df, n_splits=3, embargo_days=2, time_col=None
        )
        for train_idx, val_idx in oof_splits:
            dtrain_fold = xgb.DMatrix(
                X[train_idx], label=y[train_idx], feature_names=self._feature_names
            )
            fold_model = xgb.train(
                {k: v for k, v in self.xgb_params.items() if k != "n_estimators"},
                dtrain_fold,
                num_boost_round=self.xgb_params.get("n_estimators", 100),
            )
            dval = xgb.DMatrix(X[val_idx], feature_names=self._feature_names)
            oof_preds[val_idx] = fold_model.predict(dval)

        self.calibrator.fit(oof_preds, y)
        self.is_calibrated = True

    def save(self, path: str):
        """Serialize model to disk using JSON + XGBoost native format."""
        base_path = Path(path)
        base_path.parent.mkdir(parents=True, exist_ok=True)

        # Save XGBoost booster
        xgb_path = base_path.with_suffix(".xgb.json")
        if self.xgb_model is not None:
            self.xgb_model.save_model(str(xgb_path))

        # Save Poisson component
        poisson_path = base_path.with_suffix(".poisson.json")
        self.poisson.save(str(poisson_path))

        # Save hybrid metadata
        meta = {
            "xgb_params": self.xgb_params,
            "blend_weight": self.blend_weight,
            "use_calibration": self.use_calibration,
            "_feature_names": self._feature_names,
            "_training_count": self._training_count,
            "calibrator": isotonic_to_dict(self.calibrator) if self.is_calibrated else None,
            "is_calibrated": self.is_calibrated,
        }
        meta_path = base_path.with_suffix(".meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        logger.info("Hybrid model saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "FootballHybridModel":
        """Load model from disk using JSON + XGBoost native format."""
        base_path = Path(path)

        # Load metadata
        meta_path = base_path.with_suffix(".meta.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        model = cls(
            poisson=FootballPoissonModel.load(base_path.with_suffix(".poisson.json")),
            xgb_params=meta.get("xgb_params"),
            blend_weight=meta.get("blend_weight", 0.5),
            use_calibration=meta.get("use_calibration", True),
        )
        model._feature_names = meta.get("_feature_names")
        model._training_count = meta.get("_training_count", 0)
        model.is_calibrated = meta.get("is_calibrated", False)

        if model.is_calibrated and meta.get("calibrator"):
            model.calibrator = isotonic_from_dict(meta["calibrator"])

        # Load XGBoost booster
        xgb_path = base_path.with_suffix(".xgb.json")
        if xgb_path.exists():
            model.xgb_model = xgb.Booster()
            model.xgb_model.load_model(str(xgb_path))

        logger.info("Hybrid model loaded from %s", path)
        return model
