"""
Temporal leakage detection — blocks pipeline when strict mode is enabled.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class LeakageError(Exception):
    """Raised when dataset fails temporal integrity checks."""


class LeakageDetector:
    """Detects temporal data leakage before model training or backtesting."""

    FORBIDDEN_FEATURE_PREFIXES = ("future_", "post_match_", "closing_", "final_score")

    def check_temporal_ordering(self, df: pd.DataFrame, time_col: str = "date") -> bool:
        time_col = self._resolve_time_col(df, time_col)
        if not time_col:
            return False
        series = pd.to_datetime(df[time_col])
        is_sorted = series.is_monotonic_increasing
        if not is_sorted:
            logger.warning("Dataset not chronologically sorted — leakage risk.")
        return bool(is_sorted)

    def _resolve_time_col(self, df: pd.DataFrame, time_col: str) -> Optional[str]:
        if time_col in df.columns:
            return time_col
        for alt in ("timestamp", "game_date", "match_date", "commence_time"):
            if alt in df.columns:
                return alt
        logger.error("No time column found in dataset.")
        return None

    def detect_future_features(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        threshold: float = 0.8,
    ) -> List[str]:
        suspicious: List[str] = []
        if target_col not in df.columns:
            return suspicious
        target = df[target_col]
        if target.dtype == object:
            target = target.map({"1": 1.0, "X": 0.5, "2": 0.0, "H": 1.0, "A": 0.0}).astype(float)
        for col in feature_cols:
            if col in (target_col, "home_goals", "away_goals", "result"):
                continue
            if any(col.startswith(p) for p in self.FORBIDDEN_FEATURE_PREFIXES):
                suspicious.append(col)
                continue
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            corr = abs(df[col].corr(target))
            if pd.notna(corr) and corr > threshold:
                logger.warning("Feature '%s' corr=%.2f with target — likely leakage.", col, corr)
                suspicious.append(col)
        return suspicious

    def verify_walk_forward_split(
        self,
        train: pd.DataFrame,
        test: pd.DataFrame,
        time_col: str = "date",
        embargo_days: int = 7,
    ) -> dict:
        """Ensures train ends before test with embargo gap (purged WF)."""
        tc = self._resolve_time_col(train, time_col) or "date"
        train_max = pd.to_datetime(train[tc]).max()
        test_min = pd.to_datetime(test[tc]).min()
        gap_days = (test_min - train_max).days
        ok = gap_days >= embargo_days
        return {
            "train_max": str(train_max),
            "test_min": str(test_min),
            "gap_days": gap_days,
            "embargo_required": embargo_days,
            "passed": ok,
        }

    def check_no_post_match_columns_in_features(self, df: pd.DataFrame) -> List[str]:
        """Flags outcome columns used as model inputs."""
        bad = []
        outcome_cols = {"home_goals", "away_goals", "actual_outcome", "result", "closing_odd"}
        feature_like = [c for c in df.columns if c not in ("match_id", "home_team", "away_team", "date")]
        for col in feature_like:
            if col in outcome_cols and col not in ("odd_1", "odd_X", "odd_2", "open_odd_home"):
                if col in ("home_goals", "away_goals", "actual_outcome", "result"):
                    bad.append(col)
        return bad

    def validate_training_frame(
        self,
        df: pd.DataFrame,
        time_col: str = "date",
        target_col: str = "actual_outcome",
        strict: bool = False,
    ) -> dict:
        ordered = self.check_temporal_ordering(df, time_col)
        numeric = [
            c for c in df.columns
            if c not in (time_col, target_col, "match_id", "home_team", "away_team")
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        # Exclude known outcome/odds columns from leakage correlation scan
        exclude = {
            target_col, "home_goals", "away_goals", "result", "match_id",
            "odd_1", "odd_X", "odd_2", "open_odd_home",
            "pin_close_home", "pin_close_draw", "pin_close_away", "closing_odd",
        }
        numeric = [c for c in numeric if c not in exclude]
        suspicious = self.detect_future_features(df, numeric, target_col)
        passed = ordered and len(suspicious) == 0
        result = {
            "temporal_order_ok": ordered,
            "suspicious_features": suspicious,
            "passed": passed,
            "row_count": len(df),
        }
        if strict and not passed:
            raise LeakageError(
                f"Leakage check failed: order={ordered}, suspicious={suspicious}"
            )
        return result

    def enforce_or_raise(self, df: pd.DataFrame, **kwargs) -> dict:
        return self.validate_training_frame(df, strict=True, **kwargs)


def _resolve_odds_path(path: str | Path) -> Path:
    """Resolve a requested odds dataset path, with a couple of safe fallbacks."""
    candidate = Path(path)
    if candidate.exists():
        return candidate

    if candidate.name == "matches_football.parquet":
        for alt in (
            candidate.with_name("matches_football_fdo.parquet"),
            candidate.with_name("matches_football_real_odds.parquet"),
            candidate.with_name("matches_football_backtest.parquet"),
        ):
            if alt.exists():
                logger.warning("Fallback odds path used: %s -> %s", candidate, alt)
                return alt

    raise FileNotFoundError(f"Dataset not found: {candidate}")


def check_odds_leakage(path: str | Path) -> dict:
    """
    Convenience wrapper for CLI checks against a parquet file.

    It flags any post-match / closing-odds columns that would contaminate
    training features. For the canonical football results file it falls back
    to the closest real dataset if the exact alias is not present.
    """
    resolved = _resolve_odds_path(path)
    df = pd.read_parquet(resolved)
    detector = LeakageDetector()

    suspicious_columns = []
    for col in df.columns:
        if any(col.startswith(prefix) for prefix in detector.FORBIDDEN_FEATURE_PREFIXES):
            suspicious_columns.append(col)
        elif col in {"closing_odd", "pin_close_home", "pin_close_draw", "pin_close_away"}:
            suspicious_columns.append(col)

    result = detector.validate_training_frame(df, time_col="date", target_col="actual_outcome")
    result["file"] = str(resolved)
    result["odds_suspicious_columns"] = sorted(set(suspicious_columns))
    result["passed"] = result["passed"] and not result["odds_suspicious_columns"]

    if result["passed"]:
        logger.info("Odds leakage check PASS for %s", resolved)
    else:
        logger.warning(
            "Odds leakage check FAIL for %s | suspicious=%s",
            resolved,
            result["odds_suspicious_columns"],
        )
    return result
