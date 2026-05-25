"""
Advanced ML Pipeline Module.
Handles multi-objective training, time-decay weighting, and model evaluation.
"""
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)

class AdvancedMLPipeline:
    """Multi-objective machine learning pipeline for sports betting."""
    
    def __init__(self, objective: str = "binary:logistic"):
        self.objective = objective
        self.model = None
        
    def _calculate_time_decay_weights(self, dates: pd.Series, half_life_days: float = 365.0) -> np.ndarray:
        """Calculate exponential decay weights based on recency."""
        max_date = pd.to_datetime(dates.max())
        days_diff = (max_date - pd.to_datetime(dates)).dt.days
        
        # lambda = ln(2) / half_life
        decay_rate = np.log(2) / half_life_days
        weights = np.exp(-decay_rate * days_diff)
        
        # Normalize weights to mean=1.0 for standard loss scaling
        return (weights / weights.mean()).values
        
    def train(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series, 
        dates: pd.Series,
        hyperparams: Dict[str, Any] = None
    ) -> None:
        """Train the model with time-decay weighting."""
        if hyperparams is None:
            hyperparams = {
                "max_depth": 5,
                "learning_rate": 0.05,
                "n_estimators": 200,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "objective": self.objective
            }
            
        weights = self._calculate_time_decay_weights(dates)
        
        logger.info(f"Training XGBoost model with {len(X_train)} samples")
        
        self.model = xgb.XGBClassifier(**hyperparams)
        self.model.fit(
            X_train, 
            y_train, 
            sample_weight=weights
        )
        
        logger.info("Training complete")
        
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities for the positive class."""
        if self.model is None:
            raise ValueError("Model has not been trained yet")
            
        return self.model.predict_proba(X)[:, 1]
        
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate the model using standard metrics."""
        from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss
        
        preds = self.predict_proba(X_test)
        
        return {
            "log_loss": float(log_loss(y_test, preds)),
            "roc_auc": float(roc_auc_score(y_test, preds)),
            "brier_score": float(brier_score_loss(y_test, preds))
        }
