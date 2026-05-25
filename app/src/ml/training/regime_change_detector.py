"""
Regime Change Detector for incremental model updates.

Detects when the market dynamics have shifted significantly by comparing
distributions of key features between old and new data. Only triggers model
updates when a meaningful regime change is detected, preventing harmful
updates during stable periods.

Methods:
1. PSI (Population Stability Index) — standard in credit risk, adapted for odds
2. Kolmogorov-Smirnov (KS) test — non-parametric distribution comparison
3. CLV drift — compare mean CLV between windows
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class RegimeChangeDetector:
    """
    Detects distribution shifts between reference and current data windows.

    Only flags a regime change when multiple indicators agree, reducing
    false positives from single-test volatility.
    """

    def __init__(
        self,
        psi_threshold: float = 0.25,
        ks_threshold: float = 0.10,
        clv_drift_threshold: float = 0.02,
        min_samples: int = 30,
        features: Optional[List[str]] = None,
        agreement_required: int = 2,
    ):
        """
        Args:
            psi_threshold: PSI > this triggers alert (0.25 = moderate shift)
            ks_threshold: KS statistic > this triggers alert
            clv_drift_threshold: Absolute CLV drift > this triggers alert
            min_samples: Minimum samples required in each window
            features: Columns to monitor (None = auto-detect numeric)
            agreement_required: How many of the 3 tests must flag to trigger update
        """
        self.psi_threshold = psi_threshold
        self.ks_threshold = ks_threshold
        self.clv_drift_threshold = clv_drift_threshold
        self.min_samples = min_samples
        self.features = features
        self.agreement_required = agreement_required

    def detect(
        self,
        df_reference: pd.DataFrame,
        df_current: pd.DataFrame,
        date_col: str = "date",
        clv_col: Optional[str] = "clv_pct",
    ) -> Dict[str, any]:
        """
        Compare reference vs current data and return regime change assessment.

        Returns dict with:
            regime_changed: bool — whether update should proceed
            psi_scores: dict — per-feature PSI values
            ks_scores: dict — per-feature KS statistics
            clv_drift: float — CLV mean drift
            alerts: list — which tests flagged
            confidence: str — "strong", "moderate", "weak", "none"
        """
        if len(df_reference) < self.min_samples or len(df_current) < self.min_samples:
            logger.warning(
                "Insufficient samples: ref=%d, cur=%d (min=%d)",
                len(df_reference), len(df_current), self.min_samples,
            )
            return {
                "regime_changed": False,
                "reason": "insufficient_samples",
                "confidence": "none",
            }

        # Auto-detect numeric features if not specified
        features = self.features or self._auto_features(df_reference)
        features = [f for f in features if f in df_reference.columns and f in df_current.columns]

        if not features:
            return {
                "regime_changed": False,
                "reason": "no_suitable_features",
                "confidence": "none",
            }

        alerts = []
        psi_scores = {}
        ks_scores = {}

        # PSI per feature
        for feat in features:
            ref_vals = df_reference[feat].dropna().values
            cur_vals = df_current[feat].dropna().values
            if len(ref_vals) < 10 or len(cur_vals) < 10:
                continue
            psi = self._psi(ref_vals, cur_vals)
            psi_scores[feat] = round(psi, 4)
            if psi > self.psi_threshold:
                alerts.append(f"psi_{feat}")

        # KS per feature
        for feat in features:
            ref_vals = df_reference[feat].dropna().values
            cur_vals = df_current[feat].dropna().values
            if len(ref_vals) < 10 or len(cur_vals) < 10:
                continue
            ks_stat, _ = stats.ks_2samp(ref_vals, cur_vals)
            ks_scores[feat] = round(ks_stat, 4)
            if ks_stat > self.ks_threshold:
                alerts.append(f"ks_{feat}")

        # CLV drift
        clv_drift = 0.0
        if clv_col and clv_col in df_reference.columns and clv_col in df_current.columns:
            ref_clv = df_reference[clv_col].dropna().mean()
            cur_clv = df_current[clv_col].dropna().mean()
            clv_drift = abs(cur_clv - ref_clv)
            if clv_drift > self.clv_drift_threshold:
                alerts.append("clv_drift")

        # Decision
        n_alerts = len(alerts)
        regime_changed = n_alerts >= self.agreement_required

        if n_alerts >= 3:
            confidence = "strong"
        elif n_alerts >= 2:
            confidence = "moderate"
        elif n_alerts >= 1:
            confidence = "weak"
        else:
            confidence = "none"

        logger.info(
            "Regime check: %d alerts, changed=%s, confidence=%s",
            n_alerts, regime_changed, confidence,
        )

        return {
            "regime_changed": regime_changed,
            "alerts": alerts,
            "confidence": confidence,
            "psi_scores": psi_scores,
            "ks_scores": ks_scores,
            "clv_drift": round(clv_drift, 4),
            "n_alerts": n_alerts,
            "features_checked": features,
        }

    def _auto_features(self, df: pd.DataFrame) -> List[str]:
        """Auto-detect numeric features suitable for distribution comparison."""
        candidates = []
        for col in df.columns:
            if col in {"date", "game_date", "match_id", "home_team", "away_team", "result", "actual_outcome"}:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                # Skip mostly-constant or near-empty columns
                if df[col].nunique() > 2 and df[col].notna().sum() >= 10:
                    candidates.append(col)
        # Prioritize market-relevant features
        priority = ["odd_1", "odd_X", "odd_2", "open_odd_home", "pin_close_home",
                    "pin_close_draw", "pin_close_away", "home_goals", "away_goals",
                    "exp_goals_home", "exp_goals_away"]
        ordered = [p for p in priority if p in candidates]
        ordered += [c for c in candidates if c not in ordered]
        return ordered[:10]  # Limit to top 10

    def _psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index between two distributions."""
        # Use combined min/max for consistent binning
        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())

        if min_val == max_val:
            return 0.0

        bin_edges = np.linspace(min_val, max_val, bins + 1)

        expected_counts, _ = np.histogram(expected, bins=bin_edges)
        actual_counts, _ = np.histogram(actual, bins=bin_edges)

        # Add smoothing to avoid division by zero
        expected_perc = (expected_counts + 0.5) / (expected_counts.sum() + 0.5 * bins)
        actual_perc = (actual_counts + 0.5) / (actual_counts.sum() + 0.5 * bins)

        psi = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))
        return float(psi)


class ReplayBuffer:
    """
    Maintains a rolling buffer of recent matches for periodic recalibration.

    Unlike EMA (which blends parameters), the replay buffer keeps raw data
    and allows full recalibration on a sliding window of recent history.
    """

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self.buffer: List[Dict] = []

    def add(self, df: pd.DataFrame):
        """Add new matches to the buffer, evicting oldest if over capacity."""
        records = df.to_dict("records")
        self.buffer.extend(records)
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-self.max_size:]

    def get_window(self, n: Optional[int] = None) -> pd.DataFrame:
        """Return the most recent N records as a DataFrame."""
        n = n or self.max_size
        return pd.DataFrame(self.buffer[-n:])

    def __len__(self) -> int:
        return len(self.buffer)

    def is_ready(self, min_size: int = 100) -> bool:
        return len(self.buffer) >= min_size
