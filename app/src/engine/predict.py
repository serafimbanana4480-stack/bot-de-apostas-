"""
Prediction Engine — NBA inference pipeline with XGBoost, calibration, and meta-labeling.
NO MORE random data fallback.
"""
import logging
import os
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.core.config import settings

logger = logging.getLogger("predict")


class PredictionEngine:
    """
    Handles inference using a trained model pipeline.
    Refuses to operate if no trained model exists — no synthetic fallback.
    """

    def __init__(self, model_path: str = "models/nba_unified_pipeline.joblib"):
        self.model_path = model_path
        self.artifacts = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads model artifacts from file. Fails if missing — no fallback training."""
        if not os.path.exists(self.model_path):
            raise RuntimeError(
                f"Model file {self.model_path} not found. "
                f"Train the model first with:\n"
                f"    python scripts/train_bot.py nba --source nba-api --walk-forward\n"
                f"Or use the football strategy which has pre-trained Poisson models."
            )

        try:
            from src.ml.safe_io import safe_load
            self.artifacts = safe_load(self.model_path)
            logger.info("PredictionEngine model loaded successfully (integrity verified).")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}. Please retrain the model.")

    def predict_match(
        self,
        features: Dict[str, Any],
        odds_home: float,
        odds_away: float,
    ) -> Dict[str, Any]:
        """
        Calculates probabilities, meta-label authorization, edge, and Kelly stake size.

        Args:
            features: Feature dict for the match
            odds_home: Decimal odds for home team
            odds_away: Decimal odds for away team

        Returns:
            Dict with prediction results
        """
        if self.artifacts is None:
            raise RuntimeError("Model pipeline not loaded. Cannot predict without trained model.")

        feature_cols = self.artifacts["feature_cols"]

        # Prepare input dataframe
        input_data = {}
        for col in feature_cols:
            input_data[col] = [features.get(col, 0.0)]
        df_input = pd.DataFrame(input_data)

        # 1. Primary predictions (using latest fold model)
        prim_model = self.artifacts["models"][-1]
        calibrator = self.artifacts["calibrators"][-1]

        raw_prob_home = float(prim_model.predict_proba(df_input)[0, 1])
        calibrated_prob_home = float(calibrator.predict(np.array([raw_prob_home]))[0])

        # Clip to valid range
        calibrated_prob_home = max(0.0001, min(0.9999, calibrated_prob_home))
        calibrated_prob_away = 1.0 - calibrated_prob_home

        # 2. Edge calculations
        edge_home = (calibrated_prob_home * odds_home) - 1.0
        edge_away = (calibrated_prob_away * odds_away) - 1.0

        # Determine bet side
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

        # 3. Meta-Labeling authorization
        meta_approved = False
        meta_prob = 0.5

        if bet_side is not None and len(self.artifacts.get("meta_models", [])) > 0:
            meta_model = self.artifacts["meta_models"][-1]
            meta_feats = ["elo_diff", "rest_diff", "market_overround", "odds_home", "odds_away"]
            meta_input = {}
            for col in meta_feats:
                meta_input[col] = [features.get(col, 0.0)]
            meta_input["prim_pred"] = [raw_prob_home if bet_side == "HOME" else (1.0 - raw_prob_home)]
            df_meta_input = pd.DataFrame(meta_input)
            meta_prob = float(meta_model.predict_proba(df_meta_input)[0, 1])

            if meta_prob >= 0.60:
                meta_approved = True

        # 4. Kelly stake sizing
        stake_pct = 0.0
        if bet_side is not None and meta_approved:
            raw_kelly = selected_edge / (selected_odds - 1.0) if selected_odds > 1.0 else 0.0
            kelly_mult = settings.KELLY_MULTIPLIER
            stake_pct = max(0.0, min(0.10, raw_kelly * kelly_mult))

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
            "stake_pct": stake_pct,
        }
