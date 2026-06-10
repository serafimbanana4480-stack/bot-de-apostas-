import logging
import os
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.core.config import settings

logger = logging.getLogger("predict")

class PredictionEngine:
    """
    Handles inference using the trained XGBoost, Isotonic Calibration,
    and Meta-Labeling secondary filters. Calculates expected edge and
    Kelly sizing for value betting.
    """
    def __init__(self, model_path: str = "models/nba_unified_pipeline.joblib"):
        self.model_path = model_path
        self.artifacts = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads model artifacts from file, training a fallback if missing."""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file {self.model_path} not found. Training a default baseline model on synthetic data...")
            try:
                self._train_default_model()
            except Exception as e:
                logger.error(f"Failed to train default fallback model: {e}")
                raise RuntimeError(f"Model pkl missing and auto-train failed: {e}")

        try:
            from src.ml.safe_io import safe_load
            self.artifacts = safe_load(self.model_path)
            logger.info("PredictionEngine model pipeline loaded successfully (integrity verified).")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise e

    def _train_default_model(self) -> None:
        """Helper to train a fallback model on synthetic data."""
        np.random.seed(42)
        n_samples = 60
        from datetime import datetime, timedelta
        
        dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n_samples)]
        targets = np.random.choice([0, 1], p=[0.45, 0.55], size=n_samples)
        
        feature_rows = []
        for i in range(n_samples):
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
            for j in range(70):
                feats[f"feat_{j}"] = np.random.normal(0, 1)
                
            feature_rows.append({
                "game_id": f"G{i:03d}",
                "calculated_at": dates[i],
                "target": int(targets[i]),
                "features_data": feats
            })
            
        df = pd.DataFrame(feature_rows)
        from src.models.train import ModelTrainer
        trainer = ModelTrainer(n_splits=3, mlflow_tracking_uri="sqlite:///mlflow.db")
        trainer.train_pipeline(df)

    def predict_match(self, features: Dict[str, Any], odds_home: float, odds_away: float) -> Dict[str, Any]:
        """
        Calculates probabilities, meta-label authorization, edge, and Kelly stake size.
        """
        if self.artifacts is None:
            raise RuntimeError("Model pipeline not loaded.")

        feature_cols = self.artifacts["feature_cols"]
        
        # Prepare input df
        input_data = {}
        for col in feature_cols:
            input_data[col] = [features.get(col, 0.0)]
        df_input = pd.DataFrame(input_data)

        # 1. Primary predictions (using latest fold model)
        prim_model = self.artifacts["models"][-1]
        calibrator = self.artifacts["calibrators"][-1]
        
        raw_prob_home = float(prim_model.predict_proba(df_input)[0, 1])
        calibrated_prob_home = float(calibrator.predict(np.array([raw_prob_home]))[0])
        
        # Clip to ensure valid probabilities
        calibrated_prob_home = max(0.0001, min(0.9999, calibrated_prob_home))
        calibrated_prob_away = 1.0 - calibrated_prob_home

        # 2. Edge calculations
        edge_home = (calibrated_prob_home * odds_home) - 1.0
        edge_away = (calibrated_prob_away * odds_away) - 1.0

        # Determine if we have a primary value bet candidate
        bet_side = None
        selected_edge = 0.0
        selected_prob = 0.5
        selected_odds = 1.0

        if edge_home > 0 and edge_home > edge_away:
            bet_side = "HOME"
            selected_edge = edge_home
            selected_prob = calibrated_prob_home
            selected_odds = odds_home
        elif edge_away > 0:
            bet_side = "AWAY"
            selected_edge = edge_away
            selected_prob = calibrated_prob_away
            selected_odds = odds_away

        # 3. Meta-Labeling authorization filter
        meta_approved = False
        meta_prob = 0.5

        if bet_side is not None and len(self.artifacts["meta_models"]) > 0:
            meta_model = self.artifacts["meta_models"][-1]
            
            # Re-construct meta-features
            meta_feats = ["elo_diff", "rest_diff", "market_overround", "odds_home", "odds_away"]
            meta_input = {}
            for col in meta_feats:
                meta_input[col] = [features.get(col, 0.0)]
            meta_input["prim_pred"] = [raw_prob_home if bet_side == "HOME" else (1.0 - raw_prob_home)]
            
            df_meta_input = pd.DataFrame(meta_input)
            meta_prob = float(meta_model.predict_proba(df_meta_input)[0, 1])
            
            # Authorize if meta-prob meets threshold (0.60 default from SOPs)
            if meta_prob >= 0.60:
                meta_approved = True
        else:
            # If no bet candidate or no meta-models, it's not approved or defaults to True if no meta-models trained
            meta_approved = False

        # 4. Dimension stake via Kelly Criterion
        stake_pct = 0.0
        if bet_side is not None and meta_approved:
            # Kelly: f* = (p * b - q) / b = (p * (odds - 1) - (1 - p)) / (odds - 1) = (p * odds - 1) / (odds - 1)
            # Kelly: f* = edge / (odds - 1)
            raw_kelly = selected_edge / (selected_odds - 1.0) if selected_odds > 1.0 else 0.0
            
            # Apply Kelly Multiplier (fractional Kelly) and bound
            kelly_mult = settings.KELLY_MULTIPLIER
            stake_pct = max(0.0, min(0.10, raw_kelly * kelly_mult)) # Cap max stake at 10% bankroll per game

        return {
            "raw_prob_home": raw_prob_home,
            "calibrated_prob_home": calibrated_prob_home,
            "calibrated_prob_away": calibrated_prob_away,
            "edge_home": edge_home,
            "edge_away": edge_away,
            "bet_side": bet_side,
            "expected_edge": selected_edge,
            "selected_prob": selected_prob,
            "selected_odds": selected_odds,
            "meta_approved": meta_approved,
            "meta_prob": meta_prob,
            "stake_pct": stake_pct
        }
