import hashlib
from typing import Any, Dict

import numpy as np


class ABTestingEngine:
    """
    Routes production traffic (bets) between Champion and Challenger models,
    and performs sequential statistical significance tests on ROI/PnL.
    """
    def __init__(self, champion_id: str, challenger_id: str, split_ratio: float = 0.5):
        self.champion_id = champion_id
        self.challenger_id = challenger_id
        self.split_ratio = split_ratio

    def route_event(self, event_id: str) -> str:
        """
        Deterministically routes an event to Champion or Challenger using hash of event_id.
        Ensures consistent routing for the same game across multiple requests.
        """
        event_hash = int(hashlib.md5(event_id.encode("utf-8")).hexdigest(), 16)
        value = (event_hash % 1000) / 1000.0
        
        if value < self.split_ratio:
            return self.challenger_id
        else:
            return self.champion_id


class ThompsonSamplingBandit:
    """
    Bayesian Multi-Armed Bandit using Thompson Sampling to optimize capital
    allocation dynamic routing between Champion and Challenger models.
    """
    def __init__(self, model_a_id: str, model_b_id: str):
        self.model_a_id = model_a_id
        self.model_b_id = model_b_id
        # Alpha (successes) and Beta (failures) for Beta distribution priors
        self.alphas = {model_a_id: 1.0, model_b_id: 1.0}
        self.betas = {model_a_id: 1.0, model_b_id: 1.0}

    def route_bandit(self) -> str:
        """
        Draws samples from Beta distribution for each model and routes to the winner.
        """
        sample_a = np.random.beta(self.alphas[self.model_a_id], self.betas[self.model_a_id])
        sample_b = np.random.beta(self.alphas[self.model_b_id], self.betas[self.model_b_id])
        
        if sample_b > sample_a:
            return self.model_b_id
        else:
            return self.model_a_id

    def update_feedback(self, model_id: str, won: bool) -> None:
        """
        Updates priors based on outcome success or failure.
        """
        if model_id not in self.alphas:
            return
            
        if won:
            self.alphas[model_id] += 1.0
        else:
            self.betas[model_id] += 1.0


class SequentialTTest:
    """
    Performs Wald's Sequential Probability Ratio Test (SPRT) or sequential t-test
    to compare two models' daily returns or betting outcomes.
    """
    def __init__(self):
        pass

    def evaluate_significance(self, returns_a: np.ndarray, returns_b: np.ndarray) -> Dict[str, Any]:
        """
        Runs a standard t-test approximation on two returns arrays.
        """
        arr_a = np.array(returns_a)
        arr_b = np.array(returns_b)
        
        n_a = len(arr_a)
        n_b = len(arr_b)
        
        if n_a < 5 or n_b < 5:
            return {"significant": False, "p_value": 1.0, "reason": "Insufficient samples"}
            
        mean_a = np.mean(arr_a)
        mean_b = np.mean(arr_b)
        
        var_a = np.var(arr_a, ddof=1)
        var_b = np.var(arr_b, ddof=1)
        
        # Welchs t-test
        pooled_se = np.sqrt((var_a / n_a) + (var_b / n_b))
        if pooled_se == 0:
            return {"significant": False, "p_value": 1.0, "reason": "Zero variance detected"}
            
        t_stat = (mean_b - mean_a) / pooled_se
        
        p_val = 2 * (1 - self._normal_cdf(abs(t_stat)))
        
        return {
            "mean_a": float(mean_a),
            "mean_b": float(mean_b),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "significant": bool(p_val < 0.05)
        }

    def _normal_cdf(self, x: float) -> float:
        """Approximates standard normal CDF."""
        return 0.5 * (1.0 + np.sign(x) * (1.0 - np.exp(-2.0 * x * x / np.pi))**0.5)
