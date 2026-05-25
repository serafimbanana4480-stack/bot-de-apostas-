from typing import Dict, List

import numpy as np


class EconomicLearningLoop:
    """
    Evaluates feature performance based on direct monetary contribution (ROI-per-feature).
    Helps prune features that lead to negative expected value wagers.
    """
    def __init__(self):
        self.feature_pnl: Dict[str, List[float]] = {}

    def attribute_profit(self, features: Dict[str, float], pnl: float) -> None:
        """
        Attributes the bet outcome P&L to active features.
        If a feature value is non-zero, we credit/debit the P&L to that feature's history.
        """
        for feature_name, value in features.items():
            if abs(value) > 1e-5: # Feature was active/relevant
                if feature_name not in self.feature_pnl:
                    self.feature_pnl[feature_name] = []
                self.feature_pnl[feature_name].append(pnl)

    def evaluate_features_monetary_impact(self) -> Dict[str, Dict[str, float]]:
        """
        Returns average profit and ROI metrics per feature.
        """
        evaluation = {}
        for feature, pnl_list in self.feature_pnl.items():
            arr = np.array(pnl_list)
            total_earned = np.sum(arr)
            avg_earned = np.mean(arr)
            
            # Simple feature monetary ratio: positive vs negative outcomes
            win_rate = np.mean(arr > 0)
            
            evaluation[feature] = {
                "total_monetary_contribution": float(total_earned),
                "average_contribution": float(avg_earned),
                "profitability_ratio": float(win_rate),
                "status": "KEEP" if total_earned >= 0 else "PRUNE_CANDIDATE"
            }
        return evaluation
