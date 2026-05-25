from typing import Dict

import numpy as np


class AdvancedTrainingPipeline:
    """
    Evaluates model candidates based on a multi-objective utility function:
    combining Accuracy, Probability Calibration (ECE), expected CLV edge, and Simulated ROI.
    """
    def __init__(self):
        pass

    def evaluate_candidate_fitness(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        clv_edges: np.ndarray,
        simulated_returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculates a joint fitness score for champion/challenger selection.
        """
        if len(predictions) == 0:
            return {"fitness": 0.0, "accuracy": 0.0}

        # 1. Accuracy
        preds_binary = (predictions >= 0.5).astype(int)
        accuracy = np.mean(preds_binary == actuals)
        
        # 2. Calibration (simple proxy: mean absolute error of probabilities vs actuals)
        calibration_error = np.mean(np.abs(predictions - actuals))
        calibration_score = max(0.0, 1.0 - calibration_error)
        
        # 3. Mean CLV Edge
        mean_clv = np.mean(clv_edges)
        clv_score = max(0.0, mean_clv)
        
        # 4. Simulated PnL ROI
        mean_roi = np.mean(simulated_returns) if len(simulated_returns) > 0 else 0.0
        roi_score = max(0.0, mean_roi)
        
        # Multi-objective utility:
        # 40% Accuracy, 30% Calibration, 20% CLV, 10% ROI
        fitness = (accuracy * 0.40) + (calibration_score * 0.30) + (clv_score * 0.20) + (roi_score * 0.10)
        
        return {
            "fitness": float(fitness),
            "accuracy": float(accuracy),
            "calibration_score": float(calibration_score),
            "mean_clv": float(mean_clv),
            "mean_roi": float(mean_roi)
        }
