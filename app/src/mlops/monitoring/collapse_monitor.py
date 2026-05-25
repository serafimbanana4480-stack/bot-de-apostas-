from typing import Any, Dict, List

import numpy as np


class ModelCollapseMonitor:
    """
    Monitors model output for silent model collapse (e.g., predicting 50% flat constantly).
    """
    def __init__(self, entropy_threshold: float = 0.5, unique_ratio_threshold: float = 0.15):
        self.entropy_threshold = entropy_threshold
        self.unique_ratio_threshold = unique_ratio_threshold

    def calculate_entropy(self, probabilities: np.ndarray) -> float:
        """
        Computes Shannon entropy of binary predictions.
        Low entropy suggests lack of uncertainty differentiation.
        """
        probs = np.array(probabilities)
        if len(probs) == 0:
            return 0.0
            
        # Avoid log(0)
        probs = np.clip(probs, 1e-6, 1.0 - 1e-6)
        # Binary shannon entropy per prediction
        entropy = - (probs * np.log2(probs) + (1.0 - probs) * np.log2(1.0 - probs))
        return float(np.mean(entropy))

    def evaluate_collapse(self, probabilities: List[float]) -> Dict[str, Any]:
        """
        Checks rolling window for model collapse indicators.
        """
        probs = np.array(probabilities)
        n = len(probs)
        if n < 10:
            return {"collapse_detected": False, "reason": "Insufficient samples"}
            
        entropy = self.calculate_entropy(probs)
        
        # Calculate distinct value ratio (rounded to 3 decimals to collapse floats)
        rounded_probs = np.round(probs, 3)
        unique_count = len(np.unique(rounded_probs))
        unique_ratio = unique_count / n
        
        # Standard deviation check
        std_dev = np.std(probs)
        
        collapse_detected = False
        reasons = []
        
        if entropy < self.entropy_threshold:
            collapse_detected = True
            reasons.append(f"Entropy {entropy:.4f} below threshold {self.entropy_threshold}")
            
        if unique_ratio < self.unique_ratio_threshold:
            collapse_detected = True
            reasons.append(f"Unique ratio {unique_ratio:.4f} below threshold {self.unique_ratio_threshold}")
            
        if std_dev < 0.01:
            collapse_detected = True
            reasons.append(f"Standard deviation {std_dev:.4f} is too low (stationary output)")
            
        return {
            "collapse_detected": collapse_detected,
            "entropy": entropy,
            "unique_ratio": unique_ratio,
            "std_dev": std_dev,
            "reasons": reasons
        }
