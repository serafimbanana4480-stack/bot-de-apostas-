"""
Meta-Labeling system for filtering primary model signals using market features.

Unlike the MAML meta-learner (which uses synthetic cross-sport tasks),
this MetaLabeler is trained on REAL historical data to predict whether
a primary model signal is likely to be correct given market context.

Key idea:
- Primary model (e.g., FootballPoissonModel) generates raw signals
- MetaLabeler looks at market features (line movement, sharp/retail divergence,
  odds spreads, market efficiency) and outputs P(signal is correct)
- Only bet when meta-label probability exceeds a calibrated threshold
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger("meta_labeling")


def _build_market_features(df_market: pd.DataFrame) -> pd.DataFrame:
    """
    Build meta-labeling market features from raw odds data.

    Features:
        - line_movement_home: (pin_close_home - open_odd_home) / open_odd_home
        - odds_spread: max_home - min_home across available bookmakers
        - open_vs_close_ratio: open_odd_home / pin_close_home
        - b365_vs_pin: b365_home - pin_close_home (retail vs sharp divergence)
        - market_efficiency_score: |implied_prob_open - rolling_home_win_rate|
          computed per league using only past matches (no lookahead)
    """
    df = df_market.copy()
    feats = pd.DataFrame(index=df.index)

    # 1. line_movement_home
    feats["line_movement_home"] = (
        (df["pin_close_home"] - df["open_odd_home"]) / df["open_odd_home"]
    )

    # 2. odds_spread = max - min across available bookmakers
    odds_cols = ["pin_close_home", "b365_home", "avg_home", "odd_1"]
    available = [c for c in odds_cols if c in df.columns]
    if available:
        feats["max_odds_home"] = df[available].max(axis=1)
        feats["min_odds_home"] = df[available].min(axis=1)
        feats["odds_spread"] = feats["max_odds_home"] - feats["min_odds_home"]
    else:
        feats["odds_spread"] = 0.0

    # 3. open_vs_close_ratio
    feats["open_vs_close_ratio"] = df["open_odd_home"] / df["pin_close_home"]

    # 4. b365_vs_pin divergence
    feats["b365_vs_pin"] = df["b365_home"] - df["pin_close_home"]

    # 5. market_efficiency_score (rolling, no lookahead)
    # implied probability from open odds
    feats["implied_prob_open"] = 1.0 / df["open_odd_home"]
    feats["home_win"] = (df["actual_outcome"] == "1").astype(int)

    # Need date and league for rolling computation
    if "date" in df.columns and "league" in df.columns:
        df_sorted = df.copy()
        df_sorted["_date"] = pd.to_datetime(df_sorted["date"])
        df_sorted = df_sorted.sort_values("_date")
        df_sorted["_home_win"] = (df_sorted["actual_outcome"] == "1").astype(int)
        df_sorted["_implied"] = 1.0 / df_sorted["open_odd_home"]

        # Expanding mean of home win rate per league (shifted by 1 to avoid leakage)
        rolling_win_rate = (
            df_sorted.groupby("league")["_home_win"]
            .transform(lambda s: s.shift(1).expanding(min_periods=10).mean())
        )
        # Fill early matches with global mean
        global_mean = df_sorted["_home_win"].expanding(min_periods=10).mean().shift(1)
        rolling_win_rate = rolling_win_rate.fillna(global_mean).fillna(0.45)

        df_sorted["market_efficiency_score"] = (
            df_sorted["_implied"] - rolling_win_rate
        ).abs()

        # Map back to original index
        feats["market_efficiency_score"] = df_sorted["market_efficiency_score"].reindex(
            df.index
        )
    else:
        # Fallback: simple calibration error vs dataset-wide mean
        global_home_wr = feats["home_win"].mean()
        feats["market_efficiency_score"] = (feats["implied_prob_open"] - global_home_wr).abs()

    # Additional micro-structure features
    feats["overround_home"] = 1.0 / df["odd_1"] if "odd_1" in df.columns else np.nan
    feats["pin_overround"] = 1.0 / df["pin_close_home"] if "pin_close_home" in df.columns else np.nan
    feats["closing_edge"] = feats["overround_home"] - feats["pin_overround"]

    # Clean infinities / NaNs
    feats = feats.replace([np.inf, -np.inf], np.nan)
    # Fill NaNs with median
    feats = feats.fillna(feats.median())

    # Drop helper columns that shouldn't be model inputs
    drop_cols = ["home_win", "implied_prob_open", "max_odds_home", "min_odds_home"]
    feats = feats.drop(columns=[c for c in drop_cols if c in feats.columns], errors="ignore")

    return feats


class MetaLabeler:
    """
    Meta-labeling classifier that filters primary model signals.

    Input: primary model signals + market features
    Output: probability that the signal is correct
    """

    FEATURE_COLS: List[str] = [
        "line_movement_home",
        "odds_spread",
        "open_vs_close_ratio",
        "b365_vs_pin",
        "market_efficiency_score",
        "closing_edge",
    ]

    def __init__(
        self,
        meta_learner: Optional[Any] = None,
        calibrate: bool = True,
        min_train_samples: int = 100,
    ):
        self.logger = logging.getLogger("MetaLabeler")
        self.meta_learner = meta_learner
        self.calibrate = calibrate
        self.min_train_samples = min_train_samples

        self.is_fitted = False
        self.isotonic_calibrator: Optional[IsotonicRegression] = None
        self.feature_cols: List[str] = []
        self._model_class_name: str = ""
        self._model_params: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    @classmethod
    def extract_features(cls, df_market: pd.DataFrame) -> pd.DataFrame:
        """Public helper to extract market features from raw odds DataFrame."""
        return _build_market_features(df_market)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def fit(
        self,
        df_signals: pd.DataFrame,
        df_market: pd.DataFrame,
        n_splits: int = 3,
    ) -> Dict[str, Any]:
        """
        Train the meta-learner on historical data.

        Args:
            df_signals: DataFrame with at least columns:
                - predicted_outcome (str): '1', 'X', or '2'
                - actual_outcome (str): '1', 'X', or '2'
                Optional: prob_home, prob_draw, prob_away
            df_market: DataFrame with raw odds / market columns aligned to df_signals
            n_splits: Number of temporal folds for cross-validated calibration

        Returns:
            Training summary dict
        """
        if len(df_signals) != len(df_market):
            raise ValueError(
                f"df_signals ({len(df_signals)}) and df_market ({len(df_market)}) must have same length"
            )

        if len(df_signals) < self.min_train_samples:
            raise ValueError(
                f"Need at least {self.min_train_samples} samples, got {len(df_signals)}"
            )

        # Build features
        X = self.extract_features(df_market)
        self.feature_cols = [c for c in self.FEATURE_COLS if c in X.columns]
        X = X[self.feature_cols]

        # Target: 1 if primary model was correct, 0 otherwise
        y = (df_signals["predicted_outcome"] == df_signals["actual_outcome"]).astype(int)

        # Ensure meta-learner is instantiated
        if self.meta_learner is None:
            try:
                from xgboost import XGBClassifier

                self.meta_learner = XGBClassifier(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    eval_metric="logloss",
                    random_state=42,
                    use_label_encoder=False,
                )
                self._model_class_name = "XGBClassifier"
            except ImportError:
                from sklearn.ensemble import RandomForestClassifier

                self.meta_learner = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=6,
                    min_samples_leaf=10,
                    random_state=42,
                    n_jobs=-1,
                )
                self._model_class_name = "RandomForestClassifier"

        self._model_params = self._get_model_params()

        # Temporal split for training (no shuffle)
        if "date" in df_market.columns:
            sort_idx = pd.to_datetime(df_market["date"]).argsort()
            X_sorted = X.iloc[sort_idx].reset_index(drop=True)
            y_sorted = y.iloc[sort_idx].reset_index(drop=True)
        else:
            X_sorted = X.reset_index(drop=True)
            y_sorted = y.reset_index(drop=True)

        # Fit meta-learner on full sorted data (for production use)
        self.meta_learner.fit(X_sorted, y_sorted)

        # Calibrate probabilities using TimeSeriesSplit (out-of-fold)
        if self.calibrate and len(X_sorted) >= n_splits * 30:
            oof_preds = np.zeros(len(X_sorted))
            tscv = TimeSeriesSplit(n_splits=n_splits)
            for train_idx, val_idx in tscv.split(X_sorted):
                X_tr, X_val = X_sorted.iloc[train_idx], X_sorted.iloc[val_idx]
                y_tr = y_sorted.iloc[train_idx]
                # Clone learner for OOF predictions
                cloned = self._clone_learner()
                cloned.fit(X_tr, y_tr)
                probs = cloned.predict_proba(X_val)[:, 1]
                oof_preds[val_idx] = probs

            self.isotonic_calibrator = IsotonicRegression(out_of_bounds="clip")
            # Only fit on valid predictions
            valid_mask = oof_preds > 0
            if valid_mask.sum() > 30:
                self.isotonic_calibrator.fit(oof_preds[valid_mask], y_sorted[valid_mask])

        self.is_fitted = True

        # Feature importance if available
        importance: Dict[str, float] = {}
        if hasattr(self.meta_learner, "feature_importances_"):
            importance = dict(
                zip(self.feature_cols, map(float, self.meta_learner.feature_importances_))
            )

        accuracy = float(y.mean())
        return {
            "n_samples": int(len(y)),
            "base_accuracy": round(accuracy, 4),
            "n_features": len(self.feature_cols),
            "feature_importance": importance,
            "model_class": self._model_class_name,
        }

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        signal_prob: Optional[Dict[str, float]] = None,
        market_features: Union[pd.DataFrame, Dict[str, float], None] = None,
    ) -> np.ndarray:
        """
        Return probability that the primary signal is correct.

        Args:
            signal_prob: Optional dict with primary model probabilities (for API compatibility)
            market_features: DataFrame or dict of market features.
                If dict, it is treated as a single row.

        Returns:
            1-D array of calibrated probabilities
        """
        if not self.is_fitted:
            raise RuntimeError("MetaLabeler has not been fitted yet.")

        if market_features is None:
            raise ValueError("market_features is required")

        if isinstance(market_features, dict):
            X = pd.DataFrame([market_features])
        else:
            X = market_features.copy()

        # Ensure columns match
        missing = [c for c in self.feature_cols if c not in X.columns]
        for c in missing:
            X[c] = 0.0
        X = X[self.feature_cols]

        probs = self.meta_learner.predict_proba(X)[:, 1]

        if self.isotonic_calibrator is not None:
            probs = self.isotonic_calibrator.transform(probs)

        return np.asarray(probs)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def save(self, path: str) -> None:
        """Save model to disk using joblib + JSON metadata."""
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save sklearn/xgb model with joblib
        model_path = path_obj.with_suffix(".joblib")
        joblib.dump(self.meta_learner, model_path)

        # Save metadata as JSON
        meta = {
            "is_fitted": self.is_fitted,
            "feature_cols": self.feature_cols,
            "calibrate": self.calibrate,
            "min_train_samples": self.min_train_samples,
            "model_class_name": self._model_class_name,
            "model_params": self._model_params,
            "isotonic_calibrator": MetaLabeler._isotonic_to_dict(self.isotonic_calibrator)
            if self.isotonic_calibrator is not None
            else None,
            "model_path": str(model_path.name),
        }
        meta_path = path_obj.with_suffix(".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        self.logger.info("MetaLabeler saved to %s + %s", model_path, meta_path)

    @classmethod
    def load(cls, path: str) -> "MetaLabeler":
        """Load model from disk."""
        path_obj = Path(path)
        meta_path = path_obj.with_suffix(".json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        model_path = path_obj.with_suffix(".joblib")
        meta_learner = joblib.load(model_path)

        instance = cls(
            meta_learner=meta_learner,
            calibrate=meta["calibrate"],
            min_train_samples=meta["min_train_samples"],
        )
        instance.is_fitted = meta["is_fitted"]
        instance.feature_cols = meta["feature_cols"]
        instance._model_class_name = meta.get("model_class_name", "")
        instance._model_params = meta.get("model_params", {})

        if meta.get("isotonic_calibrator"):
            instance.isotonic_calibrator = cls._isotonic_from_dict(
                meta["isotonic_calibrator"]
            )

        return instance

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _clone_learner(self):
        """Create a fresh clone of the underlying learner for OOF calibration."""
        if self._model_class_name == "XGBClassifier":
            from xgboost import XGBClassifier

            return XGBClassifier(**self._model_params)
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(**self._model_params)

    def _get_model_params(self) -> Dict[str, Any]:
        """Extract constructor params from fitted learner."""
        params: Dict[str, Any] = {}
        if hasattr(self.meta_learner, "get_params"):
            params = self.meta_learner.get_params()
        # Remove non-serializable values
        clean = {}
        for k, v in params.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                clean[k] = v
        return clean

    @staticmethod
    def _isotonic_to_dict(model: IsotonicRegression) -> Dict[str, Any]:
        return {
            "X_min_": float(model.X_min_),
            "X_max_": float(model.X_max_),
            "increasing_": bool(model.increasing_),
            "X_thresholds_": np.asarray(model.X_thresholds_).tolist(),
            "y_thresholds_": np.asarray(model.y_thresholds_).tolist(),
            "out_of_bounds": model.out_of_bounds,
        }

    @staticmethod
    def _isotonic_from_dict(data: Dict[str, Any]) -> IsotonicRegression:
        model = IsotonicRegression(out_of_bounds=data.get("out_of_bounds", "clip"))
        model.X_min_ = np.float64(data["X_min_"])
        model.X_max_ = np.float64(data["X_max_"])
        model.increasing_ = data["increasing_"]
        model.X_thresholds_ = np.array(data["X_thresholds_"], dtype=float)
        model.y_thresholds_ = np.array(data["y_thresholds_"], dtype=float)
        # Rebuild the interpolation function used by transform/predict
        model._build_f(model.X_thresholds_, model.y_thresholds_)
        return model


# ---------------------------------------------------------------------------
# Backtest helpers
# ---------------------------------------------------------------------------
def evaluate_meta_labeling(
    df_signals: pd.DataFrame,
    df_market: pd.DataFrame,
    meta_labeler: MetaLabeler,
    threshold: float = 0.55,
    stake: float = 1.0,
) -> Dict[str, Any]:
    """
    Compare backtest metrics WITH and WITHOUT meta-labeling.

    Returns dict with:
        - without: metrics when taking every primary signal
        - with: metrics when filtering by meta-label probability >= threshold
    """
    # Ensure aligned
    df_signals = df_signals.reset_index(drop=True)
    df_market = df_market.reset_index(drop=True)

    # Primary model correctness
    correct = df_signals["predicted_outcome"] == df_signals["actual_outcome"]

    # Odds taken: use closing odds corresponding to predicted outcome
    odd_map = {"1": "odd_1", "X": "odd_X", "2": "odd_2"}
    odds_taken = df_signals["predicted_outcome"].map(
        lambda x: df_market.loc[df_signals["predicted_outcome"] == x, odd_map.get(x, "odd_1")].values[0]
        if (df_signals["predicted_outcome"] == x).any()
        else 1.0
    )
    # Vectorised odds lookup
    odds_taken = pd.Series(index=df_signals.index, dtype=float)
    for outcome, col in odd_map.items():
        mask = df_signals["predicted_outcome"] == outcome
        if col in df_market.columns:
            odds_taken[mask] = df_market.loc[mask, col]
        else:
            odds_taken[mask] = 2.0

    def _metrics(mask: pd.Series) -> Dict[str, float]:
        n = int(mask.sum())
        if n == 0:
            return {"n_bets": 0, "accuracy": 0.0, "roi": 0.0, "profit": 0.0}
        acc = float(correct[mask].mean())
        profit = float((correct[mask] * (odds_taken[mask] - 1.0) - (~correct[mask]) * 1.0).sum())
        roi = profit / (n * stake)
        return {
            "n_bets": n,
            "accuracy": round(acc, 4),
            "roi": round(roi, 4),
            "profit": round(profit, 2),
        }

    without = _metrics(pd.Series(True, index=df_signals.index))

    # Meta-label probabilities
    probs = meta_labeler.predict(market_features=df_market)
    with_mask = pd.Series(probs >= threshold, index=df_signals.index)
    with_metrics = _metrics(with_mask)

    return {
        "threshold": threshold,
        "without_meta_labeling": without,
        "with_meta_labeling": with_metrics,
        "bets_filtered": without["n_bets"] - with_metrics["n_bets"],
        "accuracy_lift": round(with_metrics["accuracy"] - without["accuracy"], 4),
        "roi_lift": round(with_metrics["roi"] - without["roi"], 4),
    }
