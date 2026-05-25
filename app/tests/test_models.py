import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.models.train import ModelTrainer


def test_model_training_pipeline():
    """Verify that model training, calibration, and meta-labeling completes successfully."""
    # 1. Generate synthetic dataset matching FeaturePipeline output structure
    np.random.seed(42)
    n_samples = 60
    
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n_samples)]
    targets = np.random.choice([0, 1], p=[0.45, 0.55], size=n_samples)
    
    feature_rows = []
    for i in range(n_samples):
        # Create dict containing all required feature keys
        feats = {
            "elo_home": 1500.0 + np.random.normal(0, 50),
            "elo_away": 1500.0 + np.random.normal(0, 50),
            "elo_diff": np.random.normal(0, 100),
            "expected_win_elo": np.random.uniform(0.3, 0.7),
            "rest_home": np.random.randint(1, 7),
            "rest_away": np.random.randint(1, 7),
            "rest_diff": np.random.randint(-5, 6),
            "b2b_home": float(np.random.choice([0, 1])),
            "b2b_away": float(np.random.choice([0, 1])),
            "travel_home": np.random.uniform(0, 2000),
            "travel_away": np.random.uniform(0, 2000),
            "travel_diff": np.random.uniform(-1000, 1000),
            "implied_prob_home": 0.5 + np.random.uniform(-0.1, 0.1),
            "implied_prob_away": 0.5 + np.random.uniform(-0.1, 0.1),
            "market_overround": 0.04,
            "odds_home": 1.91,
            "odds_away": 1.91,
            "win_rate_5_diff": np.random.uniform(-0.4, 0.4)
        }
        # Add remaining features to satisfy count
        for j in range(70):
            feats[f"feat_{j}"] = np.random.normal(0, 1)
            
        feature_rows.append({
            "game_id": f"G{i:03d}",
            "calculated_at": dates[i],
            "target": int(targets[i]),
            "features_data": feats
        })
        
    features_df = pd.DataFrame(feature_rows)
    
    # 2. Run trainer
    trainer = ModelTrainer(n_splits=3, mlflow_tracking_uri="sqlite:///mlflow.db") # Use file-based URI to avoid HTTP connection timeouts during testing
    artifacts = trainer.train_pipeline(features_df)
    
    # 3. Assertions
    assert artifacts is not None
    assert "models" in artifacts
    assert "calibrators" in artifacts
    assert "meta_models" in artifacts
    assert "feature_cols" in artifacts
    
    assert len(artifacts["models"]) > 0
    assert len(artifacts["calibrators"]) > 0
    assert len(artifacts["meta_models"]) > 0
    
    # Check that model file was saved locally
    assert os.path.exists("models/nba_unified_pipeline.pkl")


def test_ufc_xgboost_model():
    """Verify that UFCXGBoostModel fits and predicts successfully using XGBClassifier."""
    from src.ml.models.ufc_xgboost import UFCXGBoostModel
    
    # 1. Create a synthetic dataset of UFC features
    np.random.seed(42)
    n_samples = 40
    
    X = pd.DataFrame({
        "elo_diff": np.random.normal(0, 100, size=n_samples),
        "reach_advantage_mult": np.random.normal(0, 5, size=n_samples),
        "ko_tko_win_rate_a": np.random.uniform(0, 0.5, size=n_samples),
        "ko_tko_loss_rate_b": np.random.uniform(0, 0.3, size=n_samples),
        "slpm_decay_a": np.random.uniform(0.8, 1.2, size=n_samples)
    })
    y = pd.Series(np.random.choice([0, 1], size=n_samples))
    
    # 2. Fit model
    model = UFCXGBoostModel()
    model.fit(X, y)
    
    # 3. Predict probabilities
    probs = model.predict_proba(X)
    
    # 4. Assertions
    assert probs.shape == (n_samples, 2)
    assert np.all(probs >= 0.0) & np.all(probs <= 1.0)
    assert np.allclose(probs.sum(axis=1), 1.0)

