"""
Leakage Detector Module.
Enforces strict temporal ordering and causal locks.
"""
import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LeakageDetector:
    """Detects temporal data leakage in datasets before training."""
    
    def __init__(self):
        pass
        
    def check_temporal_ordering(self, df: pd.DataFrame, time_col: str = "timestamp") -> bool:
        """Verify the dataset is strictly ordered by time."""
        if time_col not in df.columns:
            logger.error(f"Time column '{time_col}' missing.")
            return False
            
        is_sorted = df[time_col].is_monotonic_increasing
        if not is_sorted:
            logger.warning("Dataset is not chronologically sorted. Temporal leakage risk.")
            
        return is_sorted
        
    def detect_future_features(self, df: pd.DataFrame, feature_cols: List[str], target_col: str) -> List[str]:
        """
        Check for suspiciously high correlations between features and the target,
        which often indicates forward-looking leakage (e.g., using post-match stats).
        """
        suspicious_features = []
        
        if target_col not in df.columns:
            return []
            
        # Compute absolute correlation with target
        for col in feature_cols:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
                
            corr = abs(df[col].corr(df[target_col]))
            
            # A correlation > 0.8 is extremely suspicious in sports betting
            if corr > 0.8:
                logger.warning(f"Feature '{col}' has {corr:.2f} correlation with target. Likely leakage!")
                suspicious_features.append(col)
                
        return suspicious_features
        
    def enforce_causal_lock(self, match_timestamp: pd.Timestamp, feature_timestamp: pd.Timestamp, buffer_mins: int = 5) -> bool:
        """
        Enforce that features were strictly available BEFORE the match started.
        """
        # Feature timestamp must be before match timestamp minus buffer
        cutoff_time = match_timestamp - pd.Timedelta(minutes=buffer_mins)
        return feature_timestamp <= cutoff_time
