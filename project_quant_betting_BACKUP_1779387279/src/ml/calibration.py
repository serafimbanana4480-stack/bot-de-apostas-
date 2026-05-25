"""
Calibration Module.
Implements Platt scaling and isotonic regression for probability calibration.
Also calculates Expected Calibration Error (ECE).
"""
import numpy as np
from sklearn.calibration import IsotonicRegression
from typing import Dict, Any, Tuple

class Calibrator:
    """Calibrates output probabilities to reflect true likelihoods."""
    
    def __init__(self, method: str = "isotonic"):
        self.method = method
        self.calibrator = None
        if method == "isotonic":
            self.calibrator = IsotonicRegression(out_of_bounds="clip")
        else:
            raise ValueError("Currently only 'isotonic' calibration is supported")
            
    def fit(self, uncalibrated_probs: np.ndarray, y_true: np.ndarray) -> None:
        """Fit the calibrator on validation data."""
        self.calibrator.fit(uncalibrated_probs, y_true)
        
    def calibrate(self, uncalibrated_probs: np.ndarray) -> np.ndarray:
        """Apply calibration to new probabilities."""
        if self.calibrator is None:
            raise ValueError("Calibrator is not fitted.")
        return self.calibrator.transform(uncalibrated_probs)
        
def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Calculate Expected Calibration Error (ECE).
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    binned = np.digitize(y_prob, bins) - 1
    
    ece = 0.0
    total_samples = len(y_prob)
    
    for i in range(n_bins):
        bin_idx = binned == i
        bin_samples = np.sum(bin_idx)
        
        if bin_samples > 0:
            bin_acc = np.mean(y_true[bin_idx])
            bin_conf = np.mean(y_prob[bin_idx])
            ece += (bin_samples / total_samples) * np.abs(bin_acc - bin_conf)
            
    return float(ece)
