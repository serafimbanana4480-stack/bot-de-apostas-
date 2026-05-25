"""Tests for RegimeChangeDetector and ReplayBuffer."""
import numpy as np
import pandas as pd
import pytest

from src.ml.training.regime_change_detector import RegimeChangeDetector, ReplayBuffer


def test_regime_detector_no_change():
    """Identical distributions should not trigger regime change."""
    rng = np.random.default_rng(42)
    base = rng.normal(2.0, 0.3, 200)
    df_ref = pd.DataFrame({
        "odd_1": base[:100],
        "odd_X": base[:100] + 1.2,
    })
    df_cur = pd.DataFrame({
        "odd_1": base[100:],
        "odd_X": base[100:] + 1.2,
    })
    detector = RegimeChangeDetector(
        psi_threshold=0.35,  # Higher threshold for stability
        ks_threshold=0.15,
        agreement_required=2,
    )
    result = detector.detect(df_ref, df_cur)
    assert result["regime_changed"] is False
    assert result["confidence"] in ("none", "weak")
    assert "odd_1" in result["psi_scores"]


def test_regime_detector_strong_shift():
    """Dramatically different distributions should trigger regime change."""
    df_ref = pd.DataFrame({
        "odd_1": np.random.normal(2.0, 0.3, 100),
        "odd_X": np.random.normal(3.2, 0.4, 100),
    })
    df_cur = pd.DataFrame({
        "odd_1": np.random.normal(5.0, 1.0, 100),  # Completely different
        "odd_X": np.random.normal(6.0, 1.0, 100),
    })
    detector = RegimeChangeDetector(agreement_required=1)
    result = detector.detect(df_ref, df_cur)
    assert result["regime_changed"] is True
    assert result["confidence"] in ("moderate", "strong")
    assert len(result["alerts"]) >= 1


def test_regime_detector_insufficient_samples():
    """Too few samples should return False with reason."""
    df_ref = pd.DataFrame({"odd_1": [2.0, 2.1]})
    df_cur = pd.DataFrame({"odd_1": [2.2, 2.3]})
    detector = RegimeChangeDetector(min_samples=10)
    result = detector.detect(df_ref, df_cur)
    assert result["regime_changed"] is False
    assert result["reason"] == "insufficient_samples"


def test_regime_detector_clv_drift():
    """CLV drift should be detected when threshold is exceeded."""
    df_ref = pd.DataFrame({
        "odd_1": np.random.normal(2.0, 0.3, 100),
        "clv_pct": np.random.normal(0.02, 0.01, 100),
    })
    df_cur = pd.DataFrame({
        "odd_1": np.random.normal(2.0, 0.3, 100),
        "clv_pct": np.random.normal(-0.05, 0.01, 100),  # Strong negative drift
    })
    detector = RegimeChangeDetector(clv_drift_threshold=0.02, agreement_required=1)
    result = detector.detect(df_ref, df_cur, clv_col="clv_pct")
    assert result["regime_changed"] is True
    assert "clv_drift" in result["alerts"]
    assert result["clv_drift"] > 0.02


def test_regime_detector_agreement_required():
    """Multiple alerts required should block single-test triggers."""
    df_ref = pd.DataFrame({
        "odd_1": np.random.normal(2.0, 0.3, 100),
    })
    df_cur = pd.DataFrame({
        "odd_1": np.random.normal(3.0, 0.3, 100),  # Moderate shift
    })
    detector = RegimeChangeDetector(agreement_required=3)
    result = detector.detect(df_ref, df_cur)
    # With only 1 feature, max 2 alerts (PSI + KS), so can't reach 3
    assert result["regime_changed"] is False


def test_replay_buffer_basic():
    """Replay buffer should maintain rolling window."""
    buf = ReplayBuffer(max_size=5)
    df1 = pd.DataFrame({"a": [1, 2, 3]})
    df2 = pd.DataFrame({"a": [4, 5, 6]})
    buf.add(df1)
    assert len(buf) == 3
    buf.add(df2)
    assert len(buf) == 5  # Evicted oldest
    window = buf.get_window()
    assert len(window) == 5
    assert window["a"].tolist() == [2, 3, 4, 5, 6]


def test_replay_buffer_ready():
    """Buffer should report readiness correctly."""
    buf = ReplayBuffer(max_size=10)
    assert buf.is_ready(min_size=5) is False
    buf.add(pd.DataFrame({"a": range(5)}))
    assert buf.is_ready(min_size=5) is True
    assert buf.is_ready(min_size=10) is False
