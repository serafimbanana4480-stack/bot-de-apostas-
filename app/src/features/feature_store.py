"""
FeatureStore — Unified feature management with leakage detection.

Usage:
    store = FeatureStore()
    store.add_feature_source("xG", lambda match_id, as_of: fetch_xg(match_id, as_of))
    store.add_feature_source("elo", lambda match_id, as_of: fetch_elo(match_id, as_of))
    feats = store.get_features("match_123", datetime.now())
    report = store.validate_no_leakage(features_df, target_series)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LeakageReport:
    """Report from leakage validation."""
    has_leakage: bool
    suspicious_features: List[str]
    details: Dict[str, Any] = field(default_factory=dict)


class FeatureStore:
    """
    Centralized feature store with:
    - Named feature sources
    - Temporal feature retrieval (as_of_date)
    - Leakage detection via target correlation
    """

    def __init__(self):
        self._sources: Dict[str, Callable[[str, datetime], pd.Series]] = {}
        self._cache: Dict[str, pd.Series] = {}

    def add_feature_source(
        self, name: str, fetcher: Callable[[str, datetime], pd.Series]
    ) -> None:
        """
        Register a feature source.

        Args:
            name: Feature source name (e.g. 'xG', 'elo', 'market')
            fetcher: Callable(match_id, as_of_date) -> pd.Series of features
        """
        self._sources[name] = fetcher
        logger.info("Registered feature source: %s", name)

    def get_features(
        self, match_id: str, as_of_date: datetime
    ) -> pd.Series:
        """
        Retrieve all features for a match as of a specific date.

        Args:
            match_id: Unique match identifier
            as_of_date: Temporal cutoff — only data known before this date

        Returns:
            pd.Series with all feature values
        """
        cache_key = f"{match_id}@{as_of_date.isoformat()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        all_feats = {}
        for name, fetcher in self._sources.items():
            try:
                feats = fetcher(match_id, as_of_date)
                if isinstance(feats, pd.Series):
                    for k, v in feats.items():
                        all_feats[f"{name}_{k}"] = v
                elif isinstance(feats, dict):
                    for k, v in feats.items():
                        all_feats[f"{name}_{k}"] = v
            except Exception as e:
                logger.warning("Feature source %s failed for %s: %s", name, match_id, e)

        series = pd.Series(all_feats)
        series.name = match_id
        self._cache[cache_key] = series
        return series

    def get_features_batch(
        self,
        match_ids: List[str],
        as_of_dates: List[datetime],
    ) -> pd.DataFrame:
        """
        Batch retrieve features for multiple matches.

        Returns:
            DataFrame (matches x features)
        """
        records = []
        for mid, as_of in zip(match_ids, as_of_dates):
            feats = self.get_features(mid, as_of)
            records.append(feats)
        return pd.DataFrame(records)

    def validate_no_leakage(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        method: str = "correlation",
        threshold: float = 0.30,
    ) -> LeakageReport:
        """
        Detect potential data leakage by checking feature-target correlation.

        Args:
            features: DataFrame of features
            target: Binary target series
            method: 'correlation' or 'mutual_info'
            threshold: Absolute correlation threshold to flag leakage

        Returns:
            LeakageReport
        """
        if method == "correlation":
            numeric = features.select_dtypes(include=[np.number])
            suspicious = []
            corr_details = {}

            for col in numeric.columns:
                corr = numeric[col].corr(target)
                if pd.isna(corr):
                    continue
                corr_details[col] = float(corr)
                if abs(corr) > threshold:
                    suspicious.append(col)

            return LeakageReport(
                has_leakage=len(suspicious) > 0,
                suspicious_features=suspicious,
                details={"method": "correlation", "threshold": threshold, "correlations": corr_details},
            )

        elif method == "mutual_info":
            try:
                from sklearn.feature_selection import mutual_info_classif
            except ImportError:
                logger.warning("sklearn not available for mutual_info")
                return LeakageReport(has_leakage=False, suspicious_features=[])

            numeric = features.select_dtypes(include=[np.number]).fillna(0)
            mi = mutual_info_classif(numeric, target, random_state=42)
            mi_norm = mi / mi.max() if mi.max() > 0 else mi
            suspicious = [
                col for col, score in zip(numeric.columns, mi_norm) if score > threshold
            ]
            return LeakageReport(
                has_leakage=len(suspicious) > 0,
                suspicious_features=suspicious,
                details={"method": "mutual_info", "threshold": threshold, "scores": dict(zip(numeric.columns, mi.tolist()))},
            )

        else:
            raise ValueError(f"Unknown method: {method}")

    def build_ufc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build UFC-specific features (stub for testing)."""
        out = df.copy()
        out["reach_diff"] = out.get("reach", 0) - out.get("opp_reach", 0)
        out["stance_encoded"] = out.get("stance", "Orthodox").map({"Orthodox": 0, "Southpaw": 1, "Switch": 2}).fillna(0)
        out["takedown_def"] = out.get("takedown_def", 0.5)
        out["sig_strike_acc"] = out.get("sig_strike_acc", 0.5)
        return out

    def clear_cache(self) -> None:
        """Clear internal feature cache."""
        self._cache.clear()
