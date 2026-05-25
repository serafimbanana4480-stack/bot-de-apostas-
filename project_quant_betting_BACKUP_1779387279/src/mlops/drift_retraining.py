"""
Drift Monitoring Module.
Detects data drift in features and performance decay in models.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from scipy.stats import ks_2samp

class DriftMonitor:
    """Monitors ML models and features for drift."""
    
    def __init__(self, ks_threshold: float = 0.05):
        self.ks_threshold = ks_threshold # p-value threshold for Kolmogorov-Smirnov test
        
    def detect_feature_drift(self, ref_data: pd.DataFrame, curr_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect drift in feature distributions using the Kolmogorov-Smirnov test.
        Compares a reference window (e.g., training data) to a current window.
        """
        drift_results = {}
        drifted_features = []
        
        common_cols = set(ref_data.columns).intersection(curr_data.columns)
        
        for col in common_cols:
            if not pd.api.types.is_numeric_dtype(ref_data[col]):
                continue
                
            # Drop NaNs for the test
            ref_vals = ref_data[col].dropna()
            curr_vals = curr_data[col].dropna()
            
            if len(ref_vals) < 10 or len(curr_vals) < 10:
                continue
                
            statistic, p_value = ks_2samp(ref_vals, curr_vals)
            
            has_drift = p_value < self.ks_threshold
            if has_drift:
                drifted_features.append(col)
                
            drift_results[col] = {
                "statistic": float(statistic),
                "p_value": float(p_value),
                "drift_detected": bool(has_drift)
            }
            
        return {
            "drifted_features_count": len(drifted_features),
            "drifted_features": drifted_features,
            "details": drift_results
        }
        
    def detect_performance_decay(self, historical_roi: List[float], recent_roi: List[float]) -> bool:
        """
        Detect if recent model performance has significantly degraded compared to historical.
        """
        if len(historical_roi) < 30 or len(recent_roi) < 10:
            return False
            
        hist_mean = np.mean(historical_roi)
        hist_std = np.std(historical_roi)
        
        recent_mean = np.mean(recent_roi)
        
        # Trigger if recent mean is more than 2 standard deviations below historical mean
        if recent_mean < (hist_mean - 2 * hist_std):
            return True
            
        return False
