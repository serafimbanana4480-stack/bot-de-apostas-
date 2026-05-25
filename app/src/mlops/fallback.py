import logging
from typing import Callable

import numpy as np

logger = logging.getLogger("model_fallback")

class ModelFallback:
    """
    Guarantees production availability by intercepting Champion prediction faults (exceptions/NaNs)
    and falling back gracefully to baseline implied market probabilities.
    """
    def __init__(self, baseline_prob_func: Callable[[], float]):
        self.baseline_prob_func = baseline_prob_func

    def predict_safe(self, champion_predict_func: Callable[[], float]) -> float:
        """
        Executes prediction, defaulting to baseline on failure or NaN values.
        """
        try:
            val = champion_predict_func()
            if val is None or np.isnan(val) or not (0.0 <= val <= 1.0):
                raise ValueError(f"Invalid model prediction output: {val}")
            return float(val)
        except Exception as e:
            logger.error(f"Champion Model prediction failed, executing baseline fallback. Error: {e}")
            return float(self.baseline_prob_func())
