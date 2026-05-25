"""
Explainability Module.
Provides SHAP-based feature importance and prediction breakdowns.
"""
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List

class ModelExplainer:
    """Wrapper for SHAP explainability."""
    
    def __init__(self, model):
        self.model = model
        # Try to extract the booster if it's an XGBoost wrapper
        if hasattr(model, 'get_booster'):
            self.explainer = shap.TreeExplainer(model.get_booster())
        else:
            self.explainer = shap.TreeExplainer(model)
            
    def get_global_importance(self, X: pd.DataFrame) -> Dict[str, float]:
        """Calculate global feature importance (mean absolute SHAP values)."""
        shap_values = self.explainer.shap_values(X)
        
        # Ensure correct shape for binary classification
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
            
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance_dict = {
            col: float(val) 
            for col, val in zip(X.columns, mean_abs_shap)
        }
        
        # Sort by importance descending
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
    def explain_prediction(self, x_instance: pd.DataFrame) -> Dict[str, Any]:
        """Explain a single prediction."""
        shap_values = self.explainer.shap_values(x_instance)
        expected_value = self.explainer.expected_value
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
            expected_value = expected_value[1]
            
        if isinstance(expected_value, np.ndarray):
            expected_value = expected_value[0]
            
        contributions = {
            col: float(val) 
            for col, val in zip(x_instance.columns, shap_values[0])
        }
        
        # Sort contributions by absolute magnitude
        sorted_contributions = dict(sorted(
            contributions.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        ))
        
        # Convert log-odds to probability
        log_odds_sum = expected_value + np.sum(shap_values[0])
        prob = 1.0 / (1.0 + np.exp(-log_odds_sum))
        
        return {
            "base_value": float(expected_value),
            "final_probability": float(prob),
            "top_contributions": dict(list(sorted_contributions.items())[:5])
        }
