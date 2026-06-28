"""
NBA Sport Implementation — uses the trained XGBoost pipeline for prediction.
"""
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.core.interfaces import BaseSport, BaseFeatureEngineer, BaseModelTrainer

logger = logging.getLogger(__name__)


class NBASport(BaseSport):
    """NBA sport implementation using the XGBoost prediction pipeline."""

    @property
    def name(self) -> str:
        return "NBA"

    def __init__(self):
        self.engine = None
        self._load_engine()

    def _load_engine(self):
        try:
            from src.engine.predict import PredictionEngine
            self.engine = PredictionEngine("models/nba_unified_pipeline.joblib")
        except Exception as e:
            logger.warning(f"NBA PredictionEngine unavailable: {e}")

    def get_ingestion_pipeline(self):
        from src.ingestion.nba_data_pipeline import ingest_nba_data
        return ingest_nba_data

    def get_feature_engineer(self):
        class NBAFeatureEngineer(BaseFeatureEngineer):
            def build_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
                return raw_data
        return NBAFeatureEngineer()

    def get_model_trainer(self):
        class NBAModelTrainer(BaseModelTrainer):
            def __init__(self):
                self.engine = None

            def train(self, X: Any, y: Any) -> None:
                logger.info("NBA model requires separate training via scripts/train_bot.py")

            def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
                return {}
        return NBAModelTrainer()
