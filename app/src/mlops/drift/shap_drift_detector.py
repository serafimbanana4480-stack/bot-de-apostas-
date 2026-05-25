"""
Online SHAP feature drift detector — monitors when features stop being
predictive and should be removed from the pipeline.

Uses SHAP values to track feature importance over time. When a feature's
mean absolute SHAP value drops below a threshold (or changes significantly),
it's flagged as drifted. The pipeline can then automatically remove it.

This prevents "zombie features" — features that were useful during training
but have since become noise due to market changes.

Usage:
    from src.mlops.drift.shap_drift_detector import SHAPDriftDetector

    detector = SHAPDriftDetector(
        reference_shap=reference_shap_values,
        drift_threshold=0.5,  # 50% importance drop
    )
    result = detector.check(current_shap_values)
    # result["drifted_features"] == ["odds_spread", "rest_diff"]
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("shap_drift_detector")


class SHAPDriftDetector:
    """
    Monitors feature importance drift using SHAP values.

    Compares current SHAP values against a reference (from training time).
    Flags features whose importance has:
    1. Dropped below a threshold (feature became useless)
    2. Changed significantly (feature behavior shifted)
    3. Increased dramatically (potential data leakage)

    Can automatically suggest feature removal from the pipeline.
    """

    def __init__(
        self,
        reference_shap: Optional[Dict[str, float]] = None,
        drift_threshold: float = 0.5,
        increase_threshold: float = 3.0,
        min_importance: float = 0.01,
        window_checks: int = 5,
    ):
        """
        Args:
            reference_shap: Dict mapping feature name → mean |SHAP| from training
            drift_threshold: Feature flagged if importance drops by this fraction (0.5 = 50%)
            increase_threshold: Feature flagged if importance increases by this factor (3.0 = 3x)
            min_importance: Minimum absolute SHAP value to consider a feature relevant
            window_checks: Number of consecutive checks before confirming drift
        """
        self.reference_shap = reference_shap or {}
        self.drift_threshold = drift_threshold
        self.increase_threshold = increase_threshold
        self.min_importance = min_importance
        self.window_checks = window_checks

        self._drift_counters: Dict[str, int] = {}
        self._check_history: List[Dict[str, Any]] = []
        self._confirmed_drifts: Dict[str, str] = {}  # feature → drift_type

    def set_reference(self, shap_values: Dict[str, float]) -> None:
        """Set the reference SHAP importance (typically from training)."""
        self.reference_shap = shap_values
        logger.info("Reference SHAP set with %d features", len(shap_values))

    def check(
        self,
        current_shap: Dict[str, float],
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Check for feature importance drift.

        Args:
            current_shap: Dict mapping feature name → mean |SHAP| from recent predictions
            feature_names: Optional list of features to check (default: all in reference)

        Returns:
            Dict with drifted_features, removed_suggestions, and details
        """
        if not self.reference_shap:
            logger.warning("No reference SHAP values set — skipping drift check")
            return {"drifted_features": [], "status": "no_reference"}

        features = feature_names or list(self.reference_shap.keys())
        drifted = []
        removed_suggestions = []
        increased = []
        details = {}

        for feat in features:
            ref_val = self.reference_shap.get(feat, 0.0)
            cur_val = current_shap.get(feat, 0.0)

            if ref_val < 1e-10 and cur_val < 1e-10:
                continue  # Both zero, no drift

            detail = {
                "reference": round(ref_val, 6),
                "current": round(cur_val, 6),
                "ratio": round(cur_val / ref_val, 4) if ref_val > 1e-10 else float("inf"),
            }

            # Check 1: Importance dropped
            if ref_val > self.min_importance and cur_val < ref_val * (1.0 - self.drift_threshold):
                detail["drift_type"] = "importance_drop"
                drifted.append(feat)
                self._drift_counters[feat] = self._drift_counters.get(feat, 0) + 1

                if self._drift_counters[feat] >= self.window_checks:
                    removed_suggestions.append(feat)
                    self._confirmed_drifts[feat] = "importance_drop"
                    logger.info(
                        "Feature '%s' confirmed drifted: SHAP %.4f → %.4f (%.0f%% drop, %d consecutive)",
                        feat, ref_val, cur_val, (1 - cur_val / ref_val) * 100,
                        self._drift_counters[feat],
                    )

            # Check 2: Importance increased dramatically (potential leakage)
            elif ref_val > 1e-10 and cur_val > ref_val * self.increase_threshold:
                detail["drift_type"] = "importance_spike"
                increased.append(feat)
                self._drift_counters[feat] = self._drift_counters.get(feat, 0) + 1

                if self._drift_counters[feat] >= self.window_checks:
                    self._confirmed_drifts[feat] = "importance_spike"
                    logger.warning(
                        "Feature '%s' SHAP spiked: %.4f → %.4f (%.1fx increase) — possible leakage?",
                        feat, ref_val, cur_val, cur_val / ref_val,
                    )

            # Check 3: Feature became irrelevant
            elif cur_val < self.min_importance and ref_val > self.min_importance:
                detail["drift_type"] = "became_irrelevant"
                drifted.append(feat)
                self._drift_counters[feat] = self._drift_counters.get(feat, 0) + 1

                if self._drift_counters[feat] >= self.window_checks:
                    removed_suggestions.append(feat)
                    self._confirmed_drifts[feat] = "became_irrelevant"

            else:
                # No drift — reset counter
                self._drift_counters.pop(feat, None)

            details[feat] = detail

        result = {
            "drifted_features": drifted,
            "increased_features": increased,
            "removed_suggestions": removed_suggestions,
            "confirmed_drifts": dict(self._confirmed_drifts),
            "details": details,
            "n_features_checked": len(features),
            "timestamp": time.time(),
        }

        self._check_history.append(result)

        if drifted or increased:
            logger.info(
                "SHAP drift check: %d drifted, %d spiked, %d suggested for removal",
                len(drifted), len(increased), len(removed_suggestions),
            )

        return result

    def compute_shap_from_model(
        self,
        model: Any,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
        n_samples: int = 100,
    ) -> Dict[str, float]:
        """
        Compute mean absolute SHAP values from a model.

        Uses shap.TreeExplainer for tree-based models (XGBoost, LightGBM, CatBoost).
        Falls back to permutation importance for other models.
        """
        try:
            import shap
        except ImportError:
            logger.warning("shap not installed — using permutation importance fallback")
            return self._permutation_importance(model, X, feature_names)

        # Sample for speed
        if len(X) > n_samples:
            indices = np.random.choice(len(X), n_samples, replace=False)
            X_sample = X[indices]
        else:
            X_sample = X

        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)

            # For binary classification, take the positive class SHAP values
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

            if feature_names is None:
                feature_names = [f"feat_{i}" for i in range(len(mean_abs_shap))]

            return {name: float(val) for name, val in zip(feature_names, mean_abs_shap)}
        except Exception as e:
            logger.warning("SHAP computation failed: %s — using permutation fallback", e)
            return self._permutation_importance(model, X, feature_names)

    def _permutation_importance(
        self,
        model: Any,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Fallback: compute permutation-based importance."""
        from sklearn.inspection import permutation_importance

        try:
            y = model.predict(X)
            result = permutation_importance(model, X, y, n_repeats=5, random_state=42)
            importances = result.importances_mean

            if feature_names is None:
                feature_names = [f"feat_{i}" for i in range(len(importances))]

            # Normalize to [0, 1] range like SHAP
            max_imp = max(importances.max(), 1e-10)
            return {name: float(imp / max_imp) for name, imp in zip(feature_names, importances)}
        except Exception as e:
            logger.warning("Permutation importance failed: %s", e)
            if feature_names:
                return {name: 0.0 for name in feature_names}
            return {}

    @property
    def status(self) -> Dict[str, Any]:
        """Get current detector status."""
        return {
            "n_reference_features": len(self.reference_shap),
            "confirmed_drifts": dict(self._confirmed_drifts),
            "n_checks": len(self._check_history),
            "drift_counters": dict(self._drift_counters),
        }
