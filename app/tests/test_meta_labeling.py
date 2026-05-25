"""
Tests for the real-data MetaLabeling system.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.ml.meta_labeling import MetaLabeler, evaluate_meta_labeling


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def synthetic_market_data() -> pd.DataFrame:
    """Create synthetic market data with realistic odds columns."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    # Simulate home win rate ~45%
    actual = np.random.choice(["1", "X", "2"], size=n, p=[0.45, 0.25, 0.30])

    open_home = np.clip(np.random.normal(2.5, 1.2, size=n), 1.1, 10.0)
    pin_close = open_home * np.clip(1 + np.random.normal(0, 0.05, size=n), 0.85, 1.15)
    b365 = pin_close * np.clip(1 + np.random.normal(0, 0.03, size=n), 0.95, 1.05)
    max_odds = np.maximum(open_home, np.maximum(pin_close, b365)) * np.clip(
        1 + np.random.exponential(0.02, size=n), 1.0, 1.1
    )
    avg_odds = (open_home + pin_close + b365) / 3

    return pd.DataFrame({
        "date": dates,
        "league": np.random.choice(["PL", "SA", "FL1"], size=n),
        "open_odd_home": np.round(open_home, 2),
        "pin_close_home": np.round(pin_close, 2),
        "b365_home": np.round(b365, 2),
        "max_home": np.round(max_odds, 2),
        "avg_home": np.round(avg_odds, 2),
        "odd_1": np.round(pin_close, 2),
        "odd_X": np.round(pin_close * np.random.uniform(2.5, 4.0, size=n), 2),
        "odd_2": np.round(pin_close * np.random.uniform(1.2, 3.0, size=n), 2),
        "actual_outcome": actual,
    })


@pytest.fixture
def synthetic_signals(synthetic_market_data: pd.DataFrame) -> pd.DataFrame:
    """Create synthetic primary model signals."""
    n = len(synthetic_market_data)
    # Make predictions correlated with actual but not perfect
    preds = synthetic_market_data["actual_outcome"].copy()
    flip_mask = np.random.random(size=n) < 0.35
    outcomes = ["1", "X", "2"]
    preds.loc[flip_mask] = np.random.choice(outcomes, size=flip_mask.sum())
    return pd.DataFrame({
        "predicted_outcome": preds.values,
        "actual_outcome": synthetic_market_data["actual_outcome"].values,
        "prob_home": np.random.uniform(0.25, 0.55, size=n),
        "prob_draw": np.random.uniform(0.20, 0.35, size=n),
        "prob_away": np.random.uniform(0.25, 0.55, size=n),
    })


# ---------------------------------------------------------------------------
# MetaLabeler unit tests
# ---------------------------------------------------------------------------
def test_extract_features(synthetic_market_data: pd.DataFrame) -> None:
    feats = MetaLabeler.extract_features(synthetic_market_data)
    expected_cols = [
        "line_movement_home",
        "odds_spread",
        "open_vs_close_ratio",
        "b365_vs_pin",
        "market_efficiency_score",
        "closing_edge",
    ]
    for col in expected_cols:
        assert col in feats.columns, f"Missing feature: {col}"
    assert len(feats) == len(synthetic_market_data)
    assert not feats.isin([np.inf, -np.inf]).any().any()
    # NaNs should be filled
    assert feats.isna().sum().sum() == 0


def test_fit_and_predict(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(calibrate=True, min_train_samples=50)
    summary = model.fit(synthetic_signals, synthetic_market_data, n_splits=3)

    assert model.is_fitted
    assert summary["n_samples"] == len(synthetic_signals)
    assert summary["n_features"] > 0
    assert "feature_importance" in summary

    probs = model.predict(market_features=synthetic_market_data.iloc[:10])
    assert len(probs) == 10
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_predict_single_dict(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(calibrate=False, min_train_samples=50)
    model.fit(synthetic_signals, synthetic_market_data, n_splits=2)

    row_dict = synthetic_market_data.iloc[0].to_dict()
    probs = model.predict(market_features=row_dict)
    assert probs.shape == (1,)
    assert 0.0 <= probs[0] <= 1.0


def test_save_load_roundtrip(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(calibrate=True, min_train_samples=50)
    model.fit(synthetic_signals, synthetic_market_data, n_splits=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "meta_labeler"
        model.save(str(path))

        # Check files exist
        assert path.with_suffix(".json").exists()
        assert path.with_suffix(".joblib").exists()

        # Verify JSON metadata
        with open(path.with_suffix(".json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["is_fitted"] is True
        assert len(meta["feature_cols"]) > 0

        loaded = MetaLabeler.load(str(path))
        assert loaded.is_fitted
        assert loaded.feature_cols == model.feature_cols

        # Predictions should match
        probs_orig = model.predict(market_features=synthetic_market_data.iloc[:5])
        probs_loaded = loaded.predict(market_features=synthetic_market_data.iloc[:5])
        np.testing.assert_allclose(probs_orig, probs_loaded, rtol=1e-5)


def test_evaluate_meta_labeling(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(calibrate=False, min_train_samples=50)
    model.fit(synthetic_signals, synthetic_market_data, n_splits=2)

    metrics = evaluate_meta_labeling(
        synthetic_signals, synthetic_market_data, model, threshold=0.55
    )
    assert "without_meta_labeling" in metrics
    assert "with_meta_labeling" in metrics
    assert metrics["without_meta_labeling"]["n_bets"] == len(synthetic_signals)
    assert metrics["with_meta_labeling"]["n_bets"] <= metrics["without_meta_labeling"]["n_bets"]
    assert 0.0 <= metrics["with_meta_labeling"]["accuracy"] <= 1.0


def test_fit_insufficient_samples(synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(min_train_samples=10_000)
    fake_signals = pd.DataFrame({
        "predicted_outcome": ["1"],
        "actual_outcome": ["1"],
    })
    with pytest.raises(ValueError, match="Need at least"):
        model.fit(fake_signals, synthetic_market_data.iloc[:1])


def test_predict_before_fit_raises() -> None:
    model = MetaLabeler()
    with pytest.raises(RuntimeError, match="not been fitted"):
        model.predict(market_features={"line_movement_home": 0.0})


def test_feature_importance_present(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    model = MetaLabeler(calibrate=False, min_train_samples=50)
    summary = model.fit(synthetic_signals, synthetic_market_data, n_splits=2)
    assert summary["feature_importance"]
    for col in model.feature_cols:
        assert col in summary["feature_importance"]


def test_temporal_ordering_respected(synthetic_signals: pd.DataFrame, synthetic_market_data: pd.DataFrame) -> None:
    """Ensure that fit sorts by date when available (no shuffle)."""
    # Shuffle market data deliberately
    shuffled_market = synthetic_market_data.sample(frac=1, random_state=7).reset_index(drop=True)
    shuffled_signals = synthetic_signals.sample(frac=1, random_state=7).reset_index(drop=True)

    model = MetaLabeler(calibrate=False, min_train_samples=50)
    summary = model.fit(shuffled_signals, shuffled_market, n_splits=2)
    assert summary["n_samples"] == len(shuffled_signals)
    # Predictions should still work
    probs = model.predict(market_features=shuffled_market.iloc[:5])
    assert len(probs) == 5
