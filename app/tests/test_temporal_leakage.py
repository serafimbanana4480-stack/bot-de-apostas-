import pandas as pd

from src.features.pipeline import FeaturePipeline


def test_temporal_leakage_in_features():
    """
    Asserts causal integrity: feature calculation for a given game date 
    must not access or depend on any records dated in the future.
    """
    pipeline = FeaturePipeline()
    
    # 1. Historical games (ordered chronologically)
    games_data = [
        {"game_id": "G1", "game_date": "2026-11-01", "home_team": "BOS", "away_team": "LAL", "home_score": 100, "away_score": 90},
        {"game_id": "G2", "game_date": "2026-11-02", "home_team": "LAL", "away_team": "GSW", "home_score": 110, "away_score": 120},
        # Future game that shouldn't affect G1 or G2 calculations
        {"game_id": "G3", "game_date": "2026-11-15", "home_team": "GSW", "away_team": "BOS", "home_score": 150, "away_score": 140}
    ]
    games_df = pd.DataFrame(games_data)
    odds_df = pd.DataFrame([
        {"game_id": "G1", "home_odds": 1.90, "away_odds": 1.90},
        {"game_id": "G2", "home_odds": 1.80, "away_odds": 2.00},
        {"game_id": "G3", "home_odds": 2.20, "away_odds": 1.70}
    ])
    
    # 2. Run pipeline with all games
    full_feats = pipeline.run(games_df, odds_df)
    
    # 3. Run pipeline without the future game G3
    partial_games_df = games_df[games_df["game_id"] != "G3"]
    partial_odds_df = odds_df[odds_df["game_id"] != "G3"]
    partial_feats = pipeline.run(partial_games_df, partial_odds_df)
    
    # Verify that features for G1 and G2 are completely identical 
    # regardless of whether future game G3 is present in the dataset.
    g1_full = full_feats[full_feats["game_id"] == "G1"].iloc[0]["features_data"]
    g1_part = partial_feats[partial_feats["game_id"] == "G1"].iloc[0]["features_data"]
    
    g2_full = full_feats[full_feats["game_id"] == "G2"].iloc[0]["features_data"]
    g2_part = partial_feats[partial_feats["game_id"] == "G2"].iloc[0]["features_data"]
    
    for key in g1_full.keys():
        assert g1_full[key] == g1_part[key], f"Leakage detected in key {key} for G1"
        
    for key in g2_full.keys():
        assert g2_full[key] == g2_part[key], f"Leakage detected in key {key} for G2"
