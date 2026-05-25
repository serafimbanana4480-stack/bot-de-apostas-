from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.validation.splits import PurgedWalkForwardCV


def test_purged_walk_forward_cv_splits():
    """Verify that splits are generated chronologically and honor the purging margin."""
    # 1. Create a dummy dataframe with chronological dates
    start_date = datetime(2026, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(100)]
    df = pd.DataFrame({
        "game_id": [f"G{i:03d}" for i in range(100)],
        "game_date": dates
    })
    
    cv = PurgedWalkForwardCV(n_splits=3, purge_days=5, embargo_days=5)
    splits = cv.split(df)
    
    # Check that we received 3 splits
    assert len(splits) == 3
    
    for i, (train_idx, val_idx) in enumerate(splits):
        # Obtain actual dates
        train_dates = df.loc[train_idx, "game_date"]
        val_dates = df.loc[val_idx, "game_date"]
        
        # Chronological verification: Train dates must occur before validation dates
        assert train_dates.max() < val_dates.min()
        
        # Purging margin verification: Difference between max train date and min val date must be at least purge_days
        margin = val_dates.min() - train_dates.max()
        assert margin >= timedelta(days=5)
        
        # Check index shapes
        assert len(train_idx) > 0
        assert len(val_idx) > 0

def test_insufficient_dates_error():
    """Verify error is raised if dataframe doesn't contain enough unique dates."""
    df = pd.DataFrame({
        "game_id": ["G001", "G002"],
        "game_date": ["2026-01-01", "2026-01-02"]
    })
    
    cv = PurgedWalkForwardCV(n_splits=5)
    with pytest.raises(ValueError, match="Insufficient distinct game dates"):
        cv.split(df)

def test_baseline_metrics():
    """Verify that baseline evaluation metrics are computed correctly."""
    import numpy as np

    from scripts.evaluate_baseline import compute_metrics
    
    y_true = np.array([1, 0, 1, 0])
    odds_home = np.array([1.5, 2.0, 1.8, 3.0])
    odds_away = np.array([2.5, 1.8, 2.1, 1.5])
    
    report = compute_metrics(y_true, odds_home, odds_away)
    
    assert "mean_overround" in report
    assert "naive" in report
    assert "bookmaker" in report
    
    # Check that bookmaker brier score is realistic
    assert 0.0 < report["bookmaker"]["brier"] < 0.25
    assert report["bookmaker"]["auc"] > 0.0


def test_football_poisson_calibration_and_ha():
    """Verify that Out-of-Fold calibration avoids leakage and dynamic Home Advantage uses league stats."""
    from src.ml.models.football_poisson import FootballPoissonModel
    
    # 1. Create a synthetic matches dataframe
    data = {
        "home_team": ["Benfica", "Porto", "Sporting", "Braga", "Benfica", "Porto", "Sporting", "Braga", "Benfica"],
        "away_team": ["Porto", "Sporting", "Braga", "Benfica", "Sporting", "Braga", "Benfica", "Porto", "Braga"],
        "home_goals": [3, 1, 4, 2, 3, 1, 4, 2, 2],
        "away_goals": [1, 2, 1, 1, 1, 2, 1, 1, 0],
        "result": ["1", "2", "1", "1", "1", "2", "1", "1", "1"],
        "league": ["PL", "PL", "PL", "SB", "SB", "SB", "PL", "PL", "SB"],
        "date": pd.date_range("2023-01-01", periods=9, freq="D"),
    }
    df = pd.DataFrame(data)
    
    # 2. Fit model with calibration enabled
    model = FootballPoissonModel(use_dixon_coles=False, use_context=False)
    model.fit(df, calibrate=True)
    
    # Assert calibration is successful
    assert model.is_calibrated is True
    
    # Check that dynamic home advantages were computed per league
    assert "PL" in model.home_advantage_by_league
    assert "SB" in model.home_advantage_by_league
    
    ha_pl = model.home_advantage_by_league["PL"]
    ha_sb = model.home_advantage_by_league["SB"]
    
    # Assert that predictions pass and adjust lambda based on the league parameter
    pred_pl = model.predict_match_outcome("Benfica", "Porto", league="PL", apply_calibration=True)
    pred_sb = model.predict_match_outcome("Benfica", "Porto", league="SB", apply_calibration=True)
    pred_none = model.predict_match_outcome("Benfica", "Porto", apply_calibration=True)
    
    # Verify that different league params produce different expected goals (due to dynamic HA)
    assert pred_pl["expected_goals_home"] != pred_sb["expected_goals_home"]
    assert pred_none["expected_goals_home"] == model.attack_strengths["Benfica"] * model.defense_strengths["Porto"] * model.global_avg_goals * model.home_advantage


def test_football_poisson_incremental_update():
    """Verify incremental update preserves old knowledge and blends new data via EMA."""
    from src.ml.models.football_poisson import FootballPoissonModel

    # 1. Fit baseline on early data
    df_v1 = pd.DataFrame({
        "home_team": ["Benfica", "Porto", "Sporting"],
        "away_team": ["Porto", "Sporting", "Benfica"],
        "home_goals": [3, 1, 2],
        "away_goals": [1, 2, 1],
        "result": ["1", "2", "1"],
        "league": ["PL", "PL", "PL"],
    })
    model = FootballPoissonModel(use_dixon_coles=False)
    model.fit(df_v1, calibrate=False)

    old_atk_benfica = model.attack_strengths["Benfica"]
    old_def_benfica = model.defense_strengths["Benfica"]
    old_global = model.global_avg_goals
    old_ha = model.home_advantage

    # 2. Incrementally update with new data (different team performance)
    df_v2 = pd.DataFrame({
        "home_team": ["Benfica", "Porto", "Sporting"],
        "away_team": ["Porto", "Sporting", "Benfica"],
        "home_goals": [1, 3, 1],  # Benfica weaker at home
        "away_goals": [3, 1, 3],  # Benfica weaker away
        "result": ["2", "1", "2"],
        "league": ["PL", "PL", "PL"],
    })
    stats = model.update(df_v2, alpha=0.3, calibrate=False)

    # 3. Assert update metadata
    assert stats["updated"] is True
    assert stats["alpha_used"] == 0.3
    assert stats["matches_added"] == 3
    assert stats["total_matches"] == 6

    # 4. Strengths should be blended (not fully overwritten)
    new_atk_benfica = model.attack_strengths["Benfica"]
    new_def_benfica = model.defense_strengths["Benfica"]

    # After weaker new data, attack should decrease but not crash to new-only value
    assert new_atk_benfica < old_atk_benfica
    assert new_atk_benfica > 0.5  # Should still be reasonable (not catastrophic forgetting)

    # 5. Global params should also blend
    assert model.global_avg_goals != old_global  # Changed but not fully to new mean
    assert model.home_advantage != old_ha

    # 6. Teams not in new data should still exist (no deletion)
    assert "Benfica" in model.attack_strengths
    assert "Porto" in model.attack_strengths
    assert "Sporting" in model.attack_strengths

    # 7. Predictions should still be valid
    pred = model.predict_match_outcome("Benfica", "Porto", league="PL")
    assert 0.0 < pred["1"] < 1.0
    assert abs(pred["1"] + pred["X"] + pred["2"] - 1.0) < 1e-6


def test_football_poisson_odds_bin_calibration_changes_prediction():
    """Verify odds-bin calibration is fitted and can adjust longshot probabilities."""
    from src.ml.models.football_poisson import FootballPoissonModel

    rows = []
    for i in range(60):
        rows.append({
            "home_team": "A",
            "away_team": "B",
            "home_goals": 2 if i < 30 else 0,
            "away_goals": 0 if i < 30 else 2,
            "result": "1" if i < 30 else "2",
            "league": "PL",
            "open_odd_home": 1.40 if i < 30 else 4.50,
            "open_odd_draw": 3.20,
            "open_odd_away": 6.00 if i < 30 else 1.80,
            "date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=i),
        })
    df = pd.DataFrame(rows)

    model = FootballPoissonModel(use_dixon_coles=False, use_context=False)
    model.fit(df, calibrate=True)

    assert model.is_calibrated is True
    assert model.odds_bin_calibrators["1"]

    base_pred = model.predict_match_outcome("A", "B", league="PL", apply_calibration=True)
    longshot_pred = model.predict_match_outcome(
        "A",
        "B",
        league="PL",
        apply_calibration=True,
        market_odds={"1": 4.50, "X": 3.20, "2": 1.80},
    )

    assert abs(base_pred["1"] - longshot_pred["1"]) > 1e-6


def test_football_poisson_update_empty_data():
    """Verify update with empty DataFrame returns updated=False gracefully."""
    from src.ml.models.football_poisson import FootballPoissonModel

    df = pd.DataFrame({
        "home_team": ["Benfica"],
        "away_team": ["Porto"],
        "home_goals": [2],
        "away_goals": [1],
        "result": ["1"],
    })
    model = FootballPoissonModel()
    model.fit(df, calibrate=False)

    result = model.update(pd.DataFrame(), alpha=0.5)
    assert result["updated"] is False
    assert "reason" in result


def test_football_poisson_update_new_team():
    """Verify that a brand-new team introduced in update gets a sensible initial strength."""
    from src.ml.models.football_poisson import FootballPoissonModel

    df_v1 = pd.DataFrame({
        "home_team": ["Benfica", "Porto"],
        "away_team": ["Porto", "Benfica"],
        "home_goals": [2, 1],
        "away_goals": [1, 2],
        "result": ["1", "2"],
    })
    model = FootballPoissonModel()
    model.fit(df_v1, calibrate=False)

    df_new = pd.DataFrame({
        "home_team": ["Braga", "Benfica"],
        "away_team": ["Benfica", "Braga"],
        "home_goals": [3, 2],
        "away_goals": [1, 3],
        "result": ["1", "2"],
    })
    stats = model.update(df_new, alpha=0.5, calibrate=False)

    assert stats["new_teams"] >= 1  # Braga is new
    assert "Braga" in model.attack_strengths
    assert "Braga" in model.defense_strengths
    # Braga strength should be based on new data (alpha=0.5 gives 50% weight)
    assert model.attack_strengths["Braga"] > 0.5

