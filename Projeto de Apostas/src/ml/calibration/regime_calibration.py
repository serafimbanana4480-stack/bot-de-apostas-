"""
Per-regime calibration — separate isotonic calibration for each market regime.

Problem: Global isotonic calibration assumes the same probability mapping
for all regimes. But favorites and underdogs have different calibration
curves, and playoff games behave differently from regular season.

Solution: Fit separate IsotonicRegression calibrators for each regime
(or sub-group). The regime classifier determines which calibrator to use.

This reduces calibration error in sub-groups, especially for:
- Favorites (prob > 0.5) vs underdogs (prob < 0.5)
- Playoffs vs regular season
- High-volume vs low-volume markets

Usage:
    from src.ml.calibration.regime_calibration import RegimeCalibrator

    cal = RegimeCalibrator(regimes=["STANDARD", "PLAYOFFS", "B2B_FATIGUE"])
    cal.fit(predictions, labels, regime_labels)
    calibrated = cal.predict(predictions, regime_labels)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.calibration import IsotonicRegression

logger = logging.getLogger("regime_calibration")


class RegimeCalibrator:
    """
    Per-regime isotonic calibration.

    Fits a separate IsotonicRegression for each regime, reducing
    calibration error in sub-groups.
    """

    def __init__(
        self,
        regimes: Optional[List[str]] = None,
        min_samples_per_regime: int = 30,
        fallback_to_global: bool = True,
    ):
        """
        Args:
            regimes: List of regime names. If None, auto-detected from data.
            min_samples_per_regime: Minimum samples to fit a regime-specific calibrator
            fallback_to_global: If True, use global calibrator for regimes with too few samples
        """
        self.regimes = regimes
        self.min_samples_per_regime = min_samples_per_regime
        self.fallback_to_global = fallback_to_global

        self._calibrators: Dict[str, IsotonicRegression] = {}
        self._global_calibrator: Optional[IsotonicRegression] = None
        self._is_fitted = False
        self._regime_counts: Dict[str, int] = {}

    def fit(
        self,
        predictions: np.ndarray,
        labels: np.ndarray,
        regime_labels: np.ndarray,
    ) -> RegimeCalibrator:
        """
        Fit per-regime isotonic calibrators.

        Args:
            predictions: Raw model predictions (uncalibrated probabilities)
            labels: True labels (0 or 1)
            regime_labels: Regime label for each prediction
        """
        predictions = np.array(predictions)
        labels = np.array(labels)
        regime_labels = np.array(regime_labels)

        # Auto-detect regimes if not provided
        if self.regimes is None:
            self.regimes = list(np.unique(regime_labels))

        # Fit global calibrator as fallback
        self._global_calibrator = IsotonicRegression(out_of_bounds="clip")
        self._global_calibrator.fit(predictions, labels)

        # Fit per-regime calibrators
        for regime in self.regimes:
            mask = regime_labels == regime
            n_samples = mask.sum()
            self._regime_counts[regime] = int(n_samples)

            if n_samples < self.min_samples_per_regime:
                logger.info(
                    "Regime '%s': only %d samples (min %d) — using global calibrator",
                    regime, n_samples, self.min_samples_per_regime,
                )
                self._calibrators[regime] = self._global_calibrator
                continue

            regime_preds = predictions[mask]
            regime_labels_sub = labels[mask]

            if len(np.unique(regime_labels_sub)) < 2:
                logger.warning(
                    "Regime '%s': uniform labels — using global calibrator",
                    regime,
                )
                self._calibrators[regime] = self._global_calibrator
                continue

            cal = IsotonicRegression(out_of_bounds="clip")
            cal.fit(regime_preds, regime_labels_sub)
            self._calibrators[regime] = cal

            # Log calibration improvement
            global_cal = self._global_calibrator.predict(regime_preds)
            regime_cal = cal.predict(regime_preds)
            from sklearn.metrics import brier_score_loss
            global_brier = brier_score_loss(regime_labels_sub, global_cal)
            regime_brier = brier_score_loss(regime_labels_sub, regime_cal)
            logger.info(
                "Regime '%s': %d samples, Brier global=%.4f → regime=%.4f (%s)",
                regime, n_samples, global_brier, regime_brier,
                "improved" if regime_brier < global_brier else "no improvement",
            )

        self._is_fitted = True
        return self

    def predict(
        self,
        predictions: np.ndarray,
        regime_labels: np.ndarray,
    ) -> np.ndarray:
        """
        Apply per-regime calibration to predictions.

        Args:
            predictions: Raw model predictions
            regime_labels: Regime label for each prediction

        Returns:
            Calibrated predictions
        """
        if not self._is_fitted:
            raise RuntimeError("Call fit() first")

        predictions = np.array(predictions)
        regime_labels = np.array(regime_labels)
        calibrated = np.zeros_like(predictions)

        for regime in np.unique(regime_labels):
            mask = regime_labels == regime
            regime_preds = predictions[mask]

            if regime in self._calibrators:
                calibrated[mask] = self._calibrators[regime].predict(regime_preds)
            elif self.fallback_to_global and self._global_calibrator is not None:
                calibrated[mask] = self._global_calibrator.predict(regime_preds)
            else:
                calibrated[mask] = regime_preds  # No calibration available

        return calibrated

    def predict_single(
        self,
        prediction: float,
        regime: str,
    ) -> float:
        """Calibrate a single prediction for a given regime."""
        if not self._is_fitted:
            raise RuntimeError("Call fit() first")

        if regime in self._calibrators:
            return float(self._calibrators[regime].predict([prediction])[0])
        elif self._global_calibrator is not None:
            return float(self._global_calibrator.predict([prediction])[0])
        return prediction

    def get_calibration_curves(self, n_points: int = 100) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Get the calibration curves for each regime.

        Returns:
            Dict mapping regime name to (input_probs, calibrated_probs) arrays
        """
        if not self._is_fitted:
            raise RuntimeError("Call fit() first")

        curves = {}
        input_range = np.linspace(0.01, 0.99, n_points)

        for regime, cal in self._calibrators.items():
            calibrated = cal.predict(input_range)
            curves[regime] = (input_range, calibrated)

        # Add global curve
        if self._global_calibrator is not None:
            global_cal = self._global_calibrator.predict(input_range)
            curves["GLOBAL"] = (input_range, global_cal)

        return curves

    @property
    def status(self) -> Dict[str, Any]:
        """Get current calibrator status."""
        return {
            "is_fitted": self._is_fitted,
            "regimes": list(self._calibrators.keys()),
            "regime_counts": self._regime_counts,
            "has_global_fallback": self._global_calibrator is not None,
        }


class ConfidenceBinCalibrator:
    """
    Per-confidence-bin isotonic calibration.

    Instead of (or in addition to) regime-based calibration, this
    calibrates separately for different confidence levels:
    - 50-60%: Low confidence predictions
    - 60-70%: Moderate confidence
    - 70-80%: High confidence
    - 80-90%: Very high confidence
    - 90-100%: Extreme confidence

    This reduces calibration error because the calibration curve
    is different at different confidence levels (e.g., predictions
    near 0.5 are typically less reliable than predictions near 0.9).
    """

    def __init__(
        self,
        bins: Optional[List[Tuple[float, float]]] = None,
        min_samples_per_bin: int = 30,
    ):
        """
        Args:
            bins: List of (lower, upper) probability bounds for each bin.
                  Default: [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
            min_samples_per_bin: Minimum samples to fit a bin-specific calibrator
        """
        self.bins = bins or [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
        self.min_samples_per_bin = min_samples_per_bin

        self._calibrators: Dict[str, IsotonicRegression] = {}
        self._global_calibrator: Optional[IsotonicRegression] = None
        self._is_fitted = False

    def _get_bin_label(self, prob: float) -> str:
        """Get the bin label for a given probability."""
        for lower, upper in self.bins:
            if lower <= prob < upper:
                return f"{lower:.1f}-{upper:.1f}"
        # Edge case: prob == 1.0
        if prob >= self.bins[-1][1]:
            return f"{self.bins[-1][0]:.1f}-{self.bins[-1][1]:.1f}"
        return "other"

    def fit(self, predictions: np.ndarray, labels: np.ndarray) -> ConfidenceBinCalibrator:
        """Fit per-confidence-bin calibrators."""
        predictions = np.array(predictions)
        labels = np.array(labels)

        # Global calibrator as fallback
        self._global_calibrator = IsotonicRegression(out_of_bounds="clip")
        self._global_calibrator.fit(predictions, labels)

        # Per-bin calibrators
        for lower, upper in self.bins:
            bin_label = f"{lower:.1f}-{upper:.1f}"
            mask = (predictions >= lower) & (predictions < upper)
            n_samples = mask.sum()

            if n_samples < self.min_samples_per_bin:
                logger.info("Confidence bin %s: %d samples (min %d) — using global", bin_label, n_samples, self.min_samples_per_bin)
                self._calibrators[bin_label] = self._global_calibrator
                continue

            bin_preds = predictions[mask]
            bin_labels = labels[mask]

            if len(np.unique(bin_labels)) < 2:
                self._calibrators[bin_label] = self._global_calibrator
                continue

            cal = IsotonicRegression(out_of_bounds="clip")
            cal.fit(bin_preds, bin_labels)
            self._calibrators[bin_label] = cal

            from sklearn.metrics import brier_score_loss
            global_brier = brier_score_loss(bin_labels, self._global_calibrator.predict(bin_preds))
            bin_brier = brier_score_loss(bin_labels, cal.predict(bin_preds))
            logger.info("Confidence bin %s: %d samples, Brier %.4f→%.4f (%s)",
                        bin_label, n_samples, global_brier, bin_brier,
                        "improved" if bin_brier < global_brier else "no improvement")

        self._is_fitted = True
        return self

    def predict(self, predictions: np.ndarray) -> np.ndarray:
        """Apply per-confidence-bin calibration."""
        if not self._is_fitted:
            raise RuntimeError("Call fit() first")

        predictions = np.array(predictions)
        calibrated = np.zeros_like(predictions)

        for lower, upper in self.bins:
            bin_label = f"{lower:.1f}-{upper:.1f}"
            mask = (predictions >= lower) & (predictions < upper)

            if bin_label in self._calibrators:
                calibrated[mask] = self._calibrators[bin_label].predict(predictions[mask])
            elif self._global_calibrator is not None:
                calibrated[mask] = self._global_calibrator.predict(predictions[mask])
            else:
                calibrated[mask] = predictions[mask]

        # Handle edge cases (prob < 0.5 or prob >= last bin upper)
        uncalibrated = calibrated == 0
        if np.any(uncalibrated) and self._global_calibrator is not None:
            calibrated[uncalibrated] = self._global_calibrator.predict(predictions[uncalibrated])

        return calibrated
