
import pandas as pd
import pytest

from src.features.pipeline import FeaturePipeline, calculate_haversine_distance


def test_haversine_distance():
    """Verify haversine distance calculation is geometrically correct."""
    # Boston to LA coordinates
    bos = (42.366, -71.062)
    lal = (34.043, -118.266)
    
    dist = calculate_haversine_distance(bos, lal)
    # Expected distance is around 2600 miles
    assert 2500 < dist < 2700

def test_feature_pipeline_execution():
    """Verify feature pipeline successfully extracts and formats 80 features chronologically."""
    # 1. Mock games dataframe (chronological matches)
    games_data = [
        {
            "game_id": "G001",
            "game_date": "2026-11-01",
            "home_team": "BOS",
            "away_team": "LAL",
            "home_score": 110,
            "away_score": 105
        },
        {
            "game_id": "G002",
            "game_date": "2026-11-03",
            "home_team": "LAL", # LAL goes back home
            "away_team": "GSW",
            "home_score": 102,
            "away_score": 115
        },
        {
            "game_id": "G003",
            "game_date": "2026-11-05",
            "home_team": "GSW",
            "away_team": "BOS", # BOS travels to Golden State
            "home_score": 120,
            "away_score": 122
        }
    ]
    games_df = pd.DataFrame(games_data)
    
    # 2. Mock odds dataframe
    odds_data = [
        {"game_id": "G001", "home_odds": 1.91, "away_odds": 1.91},
        {"game_id": "G002", "home_odds": 1.50, "away_odds": 2.70},
        {"game_id": "G003", "home_odds": 2.10, "away_odds": 1.80}
    ]
    odds_df = pd.DataFrame(odds_data)
    
    pipeline = FeaturePipeline()
    features_df = pipeline.run(games_df, odds_df)
    
    # Assertions
    assert len(features_df) == 3
    
    # Check shape of features list
    row_0 = features_df.iloc[0]
    assert row_0["game_id"] == "G001"
    assert row_0["target"] == 1 # BOS won
    
    feats = row_0["features_data"]
    # Check that Elo features exist
    assert "elo_home" in feats
    assert "elo_away" in feats
    assert "elo_diff" in feats
    assert "expected_win_elo" in feats
    
    # Check that Rest/B2B context features exist
    assert "rest_home" in feats
    assert "rest_away" in feats
    assert "travel_home" in feats
    assert "travel_away" in feats
    
    # Check rolling win rates (e.g. for BOS on game G003 after winning G001)
    row_2 = features_df.iloc[2]
    feats_2 = row_2["features_data"]
    assert feats_2["win_rate_5_away"] > 0.5 # BOS won its previous game and is the away team here
    
    # Verify that total length is at least 80 features
    assert len(feats) >= 80

def test_stationarity_analysis():
    """Verify that stationarity test accurately detects drifting and stationary columns."""
    import numpy as np
    import pandas as pd

    from scripts.test_stationarity import perform_stationarity_tests
    
    np.random.seed(42)
    n_days = 500
    
    df = pd.DataFrame({
        "stationary_col": np.random.normal(0, 1, size=n_days),
        "drifting_col": np.random.normal(0, 1, size=n_days).cumsum()
    })
    
    results = perform_stationarity_tests(df)
    
    assert "stationary_col" in results
    assert "drifting_col" in results
    
    assert results["stationary_col"]["status"] == "STATIONARY"
    assert results["drifting_col"]["status"] == "DRIFTING"


def test_injury_modifiers_adjustment():
    """Verify that passing injury modifiers updates Elo calculations accordingly."""
    pipeline = FeaturePipeline()
    
    games_df = pd.DataFrame([{
        "game_id": "G100",
        "game_date": "2026-11-10",
        "home_team": "LAL",
        "away_team": "BOS",
        "home_score": None,
        "away_score": None
    }])
    odds_df = pd.DataFrame([{"game_id": "G100", "home_odds": 2.0, "away_odds": 2.0}])
    
    # 1. Run without modifier
    feats_normal = pipeline.run(games_df, odds_df).iloc[0]["features_data"]
    
    # 2. Run with LeBron OUT on Lakers (-12% ELO)
    feats_adjusted = pipeline.run(games_df, odds_df, injury_modifiers={"LAL": -0.12}).iloc[0]["features_data"]
    
    assert feats_adjusted["elo_home"] == pytest.approx(feats_normal["elo_home"] * 0.88)
    assert feats_adjusted["elo_diff"] < feats_normal["elo_diff"]
    assert feats_adjusted["expected_win_elo"] < feats_normal["expected_win_elo"]


def test_ufc_feature_engineering():
    """Verify that UFC feature store builds chronological Elo ratings and premium features accurately."""
    from src.features.feature_store import FeatureStore
    
    # 1. Create chronological sequence of mock fights
    fights_data = [
        {
            "date": "2026-01-01",
            "fighter_a": "Alex Pereira",
            "fighter_b": "Israel Adesanya",
            "winner": "Alex Pereira",
            "method": "KO/TKO",
            "reach_a": 79.0,
            "reach_b": 80.0,
            "slpm_a": 5.11,
            "slpm_b": 3.93,
            "sapm_a": 3.65,
            "sapm_b": 2.80
        },
        {
            "date": "2026-02-01",
            "fighter_a": "Alex Pereira",
            "fighter_b": "Jamahal Hill",
            "winner": "Alex Pereira",
            "method": "KO/TKO",
            "reach_a": 79.0,
            "reach_b": 79.0,
            "slpm_a": 5.20,
            "slpm_b": 6.90,
            "sapm_a": 3.50,
            "sapm_b": 3.20
        },
        {
            "date": "2026-03-01",
            "fighter_a": "Israel Adesanya",
            "fighter_b": "Jamahal Hill",
            "winner": "Israel Adesanya",
            "method": "Decision",
            "reach_a": 80.0,
            "reach_b": 79.0,
            "slpm_a": 4.00,
            "slpm_b": 6.80,
            "sapm_a": 2.70,
            "sapm_b": 3.30
        }
    ]
    df_fights = pd.DataFrame(fights_data)
    
    fs = FeatureStore()
    df_features = fs.build_ufc_features(df_fights)
    
    # Verify features computed chronologically
    assert len(df_features) == 3
    
    # Check fight 1: Elos should be 1500 before fight
    f1 = df_features.iloc[0]
    assert f1["elo_a"] == 1500.0
    assert f1["elo_b"] == 1500.0
    assert f1["expected_win_elo"] == 0.5
    assert f1["ko_tko_win_rate_a"] == 0.0 # No historical fights before this
    
    # Alex Pereira won f1, so his Elo should increase for f2
    f2 = df_features.iloc[1]
    assert f2["elo_a"] > 1500.0 # Pereira
    assert f2["elo_b"] == 1500.0 # Hill
    assert f2["ko_tko_win_rate_a"] == 1.0 # 1 win by KO/TKO
    assert f2["ko_tko_loss_rate_b"] == 0.0
    
    # Check reach_advantage_mult = reach_diff * slpm_diff
    # For f1: (79.0 - 80.0) * (5.11 - 3.93) = -1.0 * 1.18 = -1.18
    assert f1["reach_advantage_mult"] == pytest.approx(-1.18)


