"""
Regime classifier + automatic model switching.

Enhances the existing MarketRegimeDetector with a trained Random Forest
classifier that detects market regimes from features. The orchestrator
then selects the appropriate specialist model for each regime.

Regimes detected:
- STANDARD: Normal regular season games
- PLAYOFFS: Post-season, higher variance, different dynamics
- B2B_FATIGUE: Back-to-back games, fatigue effects
- HIGH_VOLUME: Unusual betting volume (sharp money)
- INJURY_IMPACT: Key player injuries affecting odds

Each regime has its own specialist model trained on regime-specific data.
The orchestrator uses the regime classifier to route predictions.

Usage:
    from src.ml.regime_classifier import RegimeClassifier

    clf = RegimeClassifier()
    clf.fit(X_regime, y_regime)
    regime = clf.predict(game_features)
    model = clf.get_specialist_model(regime)
"""
from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.calibration import IsotonicRegression
from sklearn.ensemble import RandomForestClassifier

from src.ml.serialization import isotonic_from_dict, isotonic_to_dict

logger = logging.getLogger("regime_classifier")


class MarketRegime(Enum):
    """Market regimes for model switching."""
    STANDARD = "STANDARD"
    PLAYOFFS = "PLAYOFFS"
    B2B_FATIGUE = "B2B_FATIGUE"
    HIGH_VOLUME = "HIGH_VOLUME"
    INJURY_IMPACT = "INJURY_IMPACT"


# Feature columns used for regime classification
REGIME_FEATURES = [
    "is_playoffs", "rest_diff", "days_rest_home", "days_rest_away",
    "betting_volume_zscore", "line_movement_pct", "sharp_score",
    "injury_impact_score", "home_advantage_pct", "odds_spread",
]


class RegimeClassifier:
    """
    Random Forest classifier for market regime detection.

    Trained on game features to predict the current regime, which
    determines which specialist model to use for prediction.
    """

    def __init__(
        self,
        model_dir: str = "models/regime",
        n_estimators: int = 200,
        max_depth: int = 6,
        min_samples_leaf: int = 10,
    ):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=42,
            class_weight="balanced",
        )
        self._is_fitted = False
        self._specialist_models: Dict[str, Any] = {}
        self._specialist_calibrators: Dict[str, IsotonicRegression] = {}
        self._regime_modifier_cache: Dict[str, float] = {}

    def _extract_features(self, game_context: Dict[str, Any]) -> np.ndarray:
        """Extract regime classification features from game context."""
        features = []
        for feat in REGIME_FEATURES:
            val = game_context.get(feat, 0.0)
            if isinstance(val, bool):
                val = float(val)
            features.append(float(val))
        return np.array(features).reshape(1, -1)

    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        feature_cols: Optional[List[str]] = None,
    ) -> RegimeClassifier:
        """
        Train the regime classifier.

        Args:
            X: Feature DataFrame
            y: Regime labels (string or MarketRegime)
            feature_cols: Feature columns to use (default: REGIME_FEATURES)
        """
        cols = feature_cols or [c for c in REGIME_FEATURES if c in X.columns]
        if not cols:
            # Fallback: use all numeric columns
            cols = [c for c in X.columns if X[c].dtype in (np.float64, np.int64, float, int)]

        X_features = X[cols].fillna(0).values

        # Convert string labels to indices
        label_map = {r.value: i for i, r in enumerate(MarketRegime)}
        if isinstance(y[0], str):
            y_encoded = np.array([label_map.get(yi, 0) for yi in y])
        elif isinstance(y[0], MarketRegime):
            y_encoded = np.array([label_map[yi.value] for yi in y])
        else:
            y_encoded = y

        self.classifier.fit(X_features, y_encoded)
        self._feature_cols = cols
        self._is_fitted = True
        self._label_map = label_map
        self._reverse_map = {v: k for k, v in label_map.items()}

        logger.info(
            "Regime classifier trained: %d samples, %d features, %d regimes",
            len(X), len(cols), len(label_map),
        )
        return self

    def predict(self, game_context: Dict[str, Any]) -> MarketRegime:
        """
        Predict the market regime for a given game context.

        Args:
            game_context: Dict with game features (is_playoffs, rest_diff, etc.)

        Returns:
            Predicted MarketRegime
        """
        if not self._is_fitted:
            # Fallback to simple heuristic (like existing MarketRegimeDetector)
            return self._heuristic_regime(game_context)

        features = self._extract_features(game_context)
        # Ensure feature dimension matches training
        if hasattr(self, "_feature_cols"):
            feat_array = np.zeros((1, len(self._feature_cols)))
            for i, col in enumerate(self._feature_cols):
                feat_array[0, i] = float(game_context.get(col, 0.0))
            features = feat_array

        pred_idx = self.classifier.predict(features)[0]
        regime_str = self._reverse_map.get(pred_idx, "STANDARD")
        return MarketRegime(regime_str)

    def predict_proba(self, game_context: Dict[str, Any]) -> Dict[str, float]:
        """Predict regime probabilities for a given game context."""
        if not self._is_fitted:
            regime = self._heuristic_regime(game_context)
            return {r.value: (1.0 if r == regime else 0.0) for r in MarketRegime}

        feat_array = np.zeros((1, len(self._feature_cols)))
        for i, col in enumerate(self._feature_cols):
            feat_array[0, i] = float(game_context.get(col, 0.0))

        probas = self.classifier.predict_proba(feat_array)[0]
        result = {}
        for idx, prob in enumerate(probas):
            regime_str = self._reverse_map.get(idx, f"UNKNOWN_{idx}")
            result[regime_str] = float(prob)
        return result

    def _heuristic_regime(self, game_context: Dict[str, Any]) -> MarketRegime:
        """Fallback heuristic when classifier is not fitted."""
        is_playoffs = game_context.get("is_playoffs", False)
        rest_diff = game_context.get("rest_diff", 0.0)
        injury_score = game_context.get("injury_impact_score", 0.0)
        volume_z = game_context.get("betting_volume_zscore", 0.0)

        if is_playoffs:
            return MarketRegime.PLAYOFFS
        if injury_score > 0.5:
            return MarketRegime.INJURY_IMPACT
        if rest_diff <= -1.0:
            return MarketRegime.B2B_FATIGUE
        if abs(volume_z) > 2.0:
            return MarketRegime.HIGH_VOLUME
        return MarketRegime.STANDARD

    def register_specialist_model(
        self,
        regime: MarketRegime,
        model: Any,
        calibrator: Optional[IsotonicRegression] = None,
    ) -> None:
        """Register a specialist model for a specific regime."""
        self._specialist_models[regime.value] = model
        if calibrator:
            self._specialist_calibrators[regime.value] = calibrator
        logger.info("Registered specialist model for regime: %s", regime.value)

    def get_specialist_model(self, regime: MarketRegime) -> Optional[Any]:
        """Get the specialist model for a regime, or None if not available."""
        return self._specialist_models.get(regime.value)

    def get_specialist_calibrator(self, regime: MarketRegime) -> Optional[IsotonicRegression]:
        """Get the specialist calibrator for a regime."""
        return self._specialist_calibrators.get(regime.value)

    def predict_with_specialist(
        self,
        game_context: Dict[str, Any],
        features: np.ndarray,
        fallback_model: Any = None,
    ) -> Dict[str, Any]:
        """
        Predict using the appropriate specialist model for the detected regime.

        Falls back to the provided fallback_model if no specialist is registered
        for the detected regime.

        Returns:
            Dict with regime, probability, model_used
        """
        regime = self.predict(game_context)
        specialist = self.get_specialist_model(regime)

        if specialist is not None:
            try:
                if hasattr(specialist, "predict_proba"):
                    prob = specialist.predict_proba(features.reshape(1, -1))[0, 1]
                elif hasattr(specialist, "predict"):
                    prob = float(specialist.predict(features.reshape(1, -1))[0])
                else:
                    prob = 0.5

                # Apply regime-specific calibration
                calibrator = self.get_specialist_calibrator(regime)
                if calibrator:
                    prob = float(calibrator.predict([prob])[0])

                return {
                    "regime": regime.value,
                    "probability": prob,
                    "model_used": "specialist",
                    "regime_confidence": self.predict_proba(game_context).get(regime.value, 0.0),
                }
            except Exception as e:
                logger.warning("Specialist model failed for %s: %s", regime.value, e)

        # Fallback to default model
        if fallback_model is not None:
            try:
                if hasattr(fallback_model, "predict_proba"):
                    prob = fallback_model.predict_proba(features.reshape(1, -1))[0, 1]
                else:
                    prob = 0.5
            except Exception:
                prob = 0.5
        else:
            prob = 0.5

        return {
            "regime": regime.value,
            "probability": prob,
            "model_used": "fallback",
            "regime_confidence": self.predict_proba(game_context).get(regime.value, 0.0),
        }

    def save(self, path: Optional[str] = None) -> str:
        """Save the regime classifier and specialist models to disk using JSON/joblib."""
        save_path = Path(path or self.model_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save classifier using sklearn's recommended format (numpy arrays + JSON metadata)
        classifier_state = {
            "is_fitted": self._is_fitted,
            "feature_cols": getattr(self, "_feature_cols", REGIME_FEATURES),
            "label_map": getattr(self, "_label_map", {}),
            "reverse_map": getattr(self, "_reverse_map", {}),
        }
        if self._is_fitted:
            # RandomForest trees can be large; use joblib for the estimator
            import joblib
            joblib.dump(self.classifier, save_path / "regime_classifier.joblib")

        with open(save_path / "regime_classifier.json", "w", encoding="utf-8") as f:
            json.dump(classifier_state, f, indent=2, default=str)

        # Save specialist models (assume they have save/load or fall back to joblib)
        for regime_name, model in self._specialist_models.items():
            model_path = save_path / f"specialist_{regime_name}.joblib"
            import joblib
            joblib.dump(model, model_path)
            # Also save calibrator if present
            calibrator = self._specialist_calibrators.get(regime_name)
            if calibrator is not None:
                cal_path = save_path / f"specialist_calibrator_{regime_name}.json"
                with open(cal_path, "w", encoding="utf-8") as f:
                    json.dump(isotonic_to_dict(calibrator), f, indent=2, default=str)

        logger.info("Regime classifier saved to %s", save_path)
        return str(save_path)

    def load(self, path: Optional[str] = None) -> "RegimeClassifier":
        """Load the regime classifier from disk."""
        load_path = Path(path or self.model_dir)

        with open(load_path / "regime_classifier.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        self._is_fitted = data["is_fitted"]
        self._feature_cols = data.get("feature_cols", REGIME_FEATURES)
        self._label_map = data.get("label_map", {})
        self._reverse_map = data.get("reverse_map", {})

        if self._is_fitted:
            import joblib
            self.classifier = joblib.load(load_path / "regime_classifier.joblib")

        # Load specialist models
        for regime in MarketRegime:
            specialist_path = load_path / f"specialist_{regime.value}.joblib"
            if specialist_path.exists():
                import joblib
                self._specialist_models[regime.value] = joblib.load(specialist_path)

            cal_path = load_path / f"specialist_calibrator_{regime.value}.json"
            if cal_path.exists():
                with open(cal_path, "r", encoding="utf-8") as f:
                    self._specialist_calibrators[regime.value] = isotonic_from_dict(json.load(f))

        logger.info("Regime classifier loaded from %s (%d specialists)", load_path, len(self._specialist_models))
        return self
