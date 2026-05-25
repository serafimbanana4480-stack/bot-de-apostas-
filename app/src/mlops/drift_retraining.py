from typing import Any, Dict, List

import numpy as np


class DriftRetrainingTrigger:
    """
    Monitors prediction calibration and closing line value (CLV) drift.
    Triggers automated retraining cycles when thresholds are violated.
    """
    def __init__(
        self, 
        window_size: int = 50, 
        max_ece_threshold: float = 0.12, 
        min_avg_clv_edge: float = 0.005
    ):
        self.window_size = window_size
        self.max_ece_threshold = max_ece_threshold
        self.min_avg_clv_edge = min_avg_clv_edge
        
        self.rolling_probabilities: List[float] = []
        self.rolling_outcomes: List[int] = []
        self.rolling_clv_edges: List[float] = []

    def record_match_result(self, predicted_prob: float, outcome_won: int, clv_edge: float):
        """
        Appends prediction metrics and evicts older items outside the rolling window.
        """
        self.rolling_probabilities.append(predicted_prob)
        self.rolling_outcomes.append(outcome_won)
        self.rolling_clv_edges.append(clv_edge)
        
        if len(self.rolling_probabilities) > self.window_size:
            self.rolling_probabilities.pop(0)
            self.rolling_outcomes.pop(0)
            self.rolling_clv_edges.pop(0)

    def check_retraining_trigger(self) -> Dict[str, Any]:
        """
        Computes calibration ECE and CLV metrics over the window to determine
        if retraining is needed.
        """
        if len(self.rolling_probabilities) < self.window_size:
            return {"trigger_retraining": False, "status": "WARM_UP_PHASE"}

        # 1. Compute calibration ECE proxy (mean absolute error of prob vs outcome)
        probs = np.array(self.rolling_probabilities)
        outcomes = np.array(self.rolling_outcomes)
        ece_proxy = float(np.mean(np.abs(probs - outcomes)))
        
        # 2. Compute average CLV edge
        avg_clv = float(np.mean(self.rolling_clv_edges))
        
        # Determine trigger states
        trigger_recalibration = ece_proxy > self.max_ece_threshold
        trigger_clv_decay = avg_clv < self.min_avg_clv_edge
        
        trigger_needed = bool(trigger_recalibration or trigger_clv_decay)
        
        return {
            "trigger_retraining": trigger_needed,
            "ece_proxy": ece_proxy,
            "avg_clv_edge": avg_clv,
            "reason": "CALIBRATION_DRIFT" if trigger_recalibration else ("CLV_DECAY" if trigger_clv_decay else "STABLE")
        }
