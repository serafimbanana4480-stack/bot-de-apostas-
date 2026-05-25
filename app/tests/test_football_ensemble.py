"""Tests for FootballEnsemble and temporal feature selection."""

import numpy as np
import pandas as pd

from src.features.selection import select_features_rfe_temporal
from src.ml.ensemble.football_ensemble import FootballEnsemble


def _make_df(n: int = 40, random_state: int = 42) -> pd.DataFrame:
    """Synthetic football match dataframe."""
    rng = np.random.default_rng(random_state)
    teams = [f"T{i}" for i in range(10)]
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "home_team": rng.choice(teams, n),
            "away_team": rng.choice(teams, n),
            "home_goals": rng.integers(0, 4, n),
            "away_goals": rng.integers(0, 4, n),
            "result": rng.choice(["1", "X", "2"], n),
            "odd_1": rng.uniform(1.5, 3.0, n).round(2),
            "odd_X": rng.uniform(2.5, 4.0, n).round(2),
            "odd_2": rng.uniform(1.5, 3.0, n).round(2),
            "date": dates,
            "actual_outcome": rng.choice(["1", "X", "2"], n),
        }
    )


# --------------------------------------------------------------------------- #
# FootballEnsemble
# --------------------------------------------------------------------------- #
def test_ensemble_fit_and_predict():
    """Ensemble should fit and emit valid 1X2 probabilities."""
    df = _make_df(50)
    ensemble = FootballEnsemble(meta_learner="logistic")
    stats = ensemble.fit(df, target_col="result")

    assert stats["trained"] is True
    assert stats["matches"] == 50
    assert ensemble.is_fitted is True
    assert ensemble.xgb_model is not None
    assert ensemble.logistic_model is not None
    assert ensemble.meta_model is not None

    pred = ensemble.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)
    assert 0.0 < pred["1"] < 1.0
    assert 0.0 < pred["X"] < 1.0
    assert 0.0 < pred["2"] < 1.0
    assert abs(pred["1"] + pred["X"] + pred["2"] - 1.0) < 1e-5
    assert "poisson_p1" in pred
    assert "xgb_p1" in pred
    assert "lr_p1" in pred


def test_ensemble_save_load(tmp_path):
    """Ensemble should round-trip through save/load without pickle."""
    df = _make_df(30)
    ensemble = FootballEnsemble(meta_learner="average")
    ensemble.fit(df, target_col="result")

    path = tmp_path / "ensemble"
    ensemble.save(str(path))
    loaded = FootballEnsemble.load(str(path))

    assert loaded.meta_learner_type == "average"
    assert loaded.is_fitted is True
    assert loaded._feature_names == ensemble._feature_names

    pred1 = ensemble.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)
    pred2 = loaded.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    assert abs(pred1["1"] - pred2["1"]) < 1e-3
    assert abs(pred1["X"] - pred2["X"]) < 1e-3
    assert abs(pred1["2"] - pred2["2"]) < 1e-3


# --------------------------------------------------------------------------- #
# Feature selection
# --------------------------------------------------------------------------- #
def test_feature_selection_reduces_dimensionality():
    """RFE with temporal split must reduce ~80 features to 15-20."""
    rng = np.random.default_rng(42)
    n_samples = 120
    n_features = 80

    X = pd.DataFrame(
        rng.standard_normal((n_samples, n_features)),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    # Inject a small amount of signal into a handful of features
    signal = (
        X["feat_0"] * 0.5
        + X["feat_1"] * 0.3
        - X["feat_2"] * 0.2
        + rng.normal(0, 0.1, n_samples)
    )
    y = np.where(signal > np.median(signal), "1", "2")

    selected = select_features_rfe_temporal(
        X, y, n_features=15, n_splits=3, random_state=42
    )

    assert isinstance(selected, list)
    assert len(selected) <= 20
    assert len(selected) >= 5
    # At least one of the true signal features should survive
    assert any(f in selected for f in {"feat_0", "feat_1", "feat_2"})
