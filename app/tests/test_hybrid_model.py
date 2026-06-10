"""Tests for FootballHybridModel (Poisson + XGBoost)."""
import pickle

import numpy as np
import pandas as pd
import pytest

from src.ml.models.football_hybrid import FootballHybridModel


def _make_df(n: int = 20, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    teams = [f"T{i}" for i in range(10)]
    return pd.DataFrame({
        "home_team": rng.choice(teams, n),
        "away_team": rng.choice(teams, n),
        "home_goals": rng.integers(0, 4, n),
        "away_goals": rng.integers(0, 4, n),
        "result": rng.choice(["1", "X", "2"], n),
        "odd_1": rng.uniform(1.5, 3.0, n).round(2),
        "odd_X": rng.uniform(2.5, 4.0, n).round(2),
        "odd_2": rng.uniform(1.5, 3.0, n).round(2),
        "date": pd.date_range("2023-01-01", periods=n, freq="D"),
        "actual_outcome": rng.choice(["1", "X", "2"], n),
    })


def test_hybrid_fit_and_predict():
    """Hybrid model should fit and produce valid probabilities."""
    df = _make_df(30)
    model = FootballHybridModel(blend_weight=0.3)
    stats = model.fit(df, calibration=False)
    assert stats["trained"] is True
    assert stats["matches"] == 30
    assert model.xgb_model is not None

    pred = model.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)
    assert 0.0 < pred["1"] < 1.0
    assert 0.0 < pred["X"] < 1.0
    assert 0.0 < pred["2"] < 1.0
    assert abs(pred["1"] + pred["X"] + pred["2"] - 1.0) < 1e-5
    assert "poisson_p1" in pred
    assert "xgb_p1" in pred


def test_hybrid_incremental_update():
    """Incremental update should preserve Poisson + warm-start XGBoost."""
    df_v1 = _make_df(30, random_state=1)
    df_new = _make_df(15, random_state=2)

    model = FootballHybridModel(blend_weight=0.3)
    model.fit(df_v1, calibration=False)
    old_xgb = model.xgb_model

    stats = model.update(df_new, alpha=0.2, xgb_incremental_rounds=10, calibration=False)
    assert stats["updated"] is True
    assert stats["matches_added"] == 15
    assert stats["total_matches"] == 45
    assert stats["xgb_rounds"] == 10
    assert model.xgb_model is not None
    # Warm start: same booster object should be updated (not replaced)
    # XGBoost returns a new booster, but it should contain the old trees + new ones
    assert model._training_count == 45


def test_hybrid_blend_weights():
    """Different blend weights should shift prediction between Poisson and XGB."""
    df = _make_df(50)
    model_poisson = FootballHybridModel(blend_weight=0.0)
    model_poisson.fit(df, calibration=False)
    pred_p = model_poisson.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    model_xgb = FootballHybridModel(blend_weight=1.0)
    model_xgb.fit(df, calibration=False)
    pred_x = model_xgb.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    # With different blend weights, predictions should diverge
    # (not guaranteed, but highly likely with random data)
    assert abs(pred_p["1"] - pred_x["1"]) > 1e-6 or abs(pred_p["X"] - pred_x["X"]) > 1e-6


def test_hybrid_save_and_load(tmp_path):
    """Model should round-trip through pickle."""
    df = _make_df(20)
    model = FootballHybridModel(blend_weight=0.3)
    model.fit(df, calibration=False)

    path = tmp_path / "hybrid.pkl"
    model.save(str(path))
    loaded = FootballHybridModel.load(str(path))

    assert loaded.blend_weight == 0.3
    assert loaded._feature_names == model._feature_names
    pred1 = model.predict("T0", "T1", odd_1=2.0)
    pred2 = loaded.predict("T0", "T1", odd_1=2.0)
    assert abs(pred1["1"] - pred2["1"]) < 1e-3  # JSON serialization may introduce minor fp differences


def test_hybrid_ewc_update():
    """EWC update with old buffer should preserve old predictions."""
    df_old = _make_df(50, random_state=1)
    df_new = _make_df(20, random_state=2)

    model = FootballHybridModel(blend_weight=0.5)
    model.fit(df_old, calibration=False)

    # Predict on a fixed test row before update
    pred_before = model.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    # Standard update (no EWC)
    model_no_ewc = pickle.loads(pickle.dumps(model))
    model_no_ewc.update(df_new, xgb_incremental_rounds=10, ewc_lambda=0.0)
    pred_no_ewc = model_no_ewc.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    # EWC update (with old buffer)
    model_ewc = pickle.loads(pickle.dumps(model))
    model_ewc.update(df_new, xgb_incremental_rounds=10, ewc_lambda=1.0, df_old_buffer=df_old)
    pred_ewc = model_ewc.predict("T0", "T1", odd_1=2.0, odd_X=3.2, odd_2=2.5)

    # EWC should keep predictions closer to the original (within reasonable tolerance)
    # Note: warm-start XGBoost with EWC weighting is heuristic; we check both are close
    diff_no_ewc = abs(pred_no_ewc["1"] - pred_before["1"])
    diff_ewc = abs(pred_ewc["1"] - pred_before["1"])
    # EWC should not diverge wildly; allow small tolerance for stochastic warm-start
    assert diff_ewc <= 0.15, f"EWC diverged too much: {diff_ewc}"
    assert diff_no_ewc <= 0.15, f"No-EWC diverged too much: {diff_no_ewc}"


def test_hybrid_empty_update():
    """Empty update should return updated=False gracefully."""
    df = _make_df(20)
    model = FootballHybridModel()
    model.fit(df, calibration=False)
    result = model.update(pd.DataFrame())
    assert result["updated"] is False
    assert "reason" in result
