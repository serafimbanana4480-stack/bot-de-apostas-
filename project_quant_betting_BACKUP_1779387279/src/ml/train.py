"""
Model Training Module.
Handles the end-to-end training process.
"""
import logging
from typing import Dict, Any, Tuple
import pandas as pd
from src.ml.advanced_pipeline import AdvancedMLPipeline
from src.ml.calibration import Calibrator, calculate_ece

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Orchestrates model training, evaluation, and calibration."""
    
    def __init__(self):
        self.pipeline = AdvancedMLPipeline()
        self.calibrator = Calibrator()
        
    def train_and_evaluate(
        self, 
        X_train: pd.DataFrame, 
        y_train: pd.Series, 
        dates_train: pd.Series,
        X_val: pd.DataFrame, 
        y_val: pd.Series
    ) -> Dict[str, float]:
        """Train the model, fit the calibrator, and return evaluation metrics."""
        
        # 1. Train Model
        logger.info("Starting model training...")
        self.pipeline.train(X_train, y_train, dates_train)
        
        # 2. Get uncalibrated probabilities for validation set
        uncalibrated_val_probs = self.pipeline.predict_proba(X_val)
        
        # 3. Fit Calibrator
        logger.info("Fitting calibrator...")
        self.calibrator.fit(uncalibrated_val_probs, y_val)
        
        # 4. Evaluate (Calibrated)
        calibrated_val_probs = self.calibrator.calibrate(uncalibrated_val_probs)
        
        from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss
        
        metrics = {
            "log_loss": float(log_loss(y_val, calibrated_val_probs)),
            "roc_auc": float(roc_auc_score(y_val, calibrated_val_probs)),
            "brier_score": float(brier_score_loss(y_val, calibrated_val_probs)),
            "ece": calculate_ece(y_val.values, calibrated_val_probs)
        }
        
        logger.info(f"Evaluation Metrics: {metrics}")
        return metrics
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """End-to-end prediction with calibration applied."""
        uncalibrated = self.pipeline.predict_proba(X)
        return self.calibrator.calibrate(uncalibrated)
