from typing import Any, Dict, List

import numpy as np


class MarkowitzPortfolioOptimizer:
    """
    Optimizes capital allocation across correlated bets using Mean-Variance optimization
    with covariance shrinkage (Ledoit-Wolf style) to maximize Sharpe Ratio.
    """
    def __init__(self, risk_aversion_lambda: float = 2.0, max_bet_exposure: float = 0.08):
        self.risk_aversion = risk_aversion_lambda
        self.max_bet_exposure = max_bet_exposure

    def apply_covariance_shrinkage(self, sample_cov: np.ndarray, shrinkage_target: float = 0.1) -> np.ndarray:
        """
        Shrinks sample covariance matrix towards a diagonal target matrix to reduce noise.
        ShrunkCov = (1 - target) * SampleCov + target * Diagonal(SampleCov)
        """
        diag = np.diag(np.diag(sample_cov))
        return (1.0 - shrinkage_target) * sample_cov + shrinkage_target * diag

    def optimize_allocation(
        self, 
        bets: List[Dict[str, Any]], 
        covariance_matrix: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Solves the quadratic optimization problem to allocate optimal stakes.
        Maximize: w.T * mu - (lambda/2) * w.T * Cov * w
        Subject to: 0 <= w_i <= max_bet_exposure
        """
        n = len(bets)
        if n == 0:
            return []
            
        mu = np.array([bet["ev"] for bet in bets])
        
        # Apply shrinkage to covariance matrix
        cov = self.apply_covariance_shrinkage(covariance_matrix)
        
        # Iterative solver: simple gradient ascent projection to handle bounds constraint 0 <= w_i <= max_bet_exposure
        weights = np.zeros(n)
        learning_rate = 0.05
        epochs = 100
        
        for _ in range(epochs):
            # Gradient: mu - lambda * Cov * weights
            grad = mu - self.risk_aversion * np.dot(cov, weights)
            # Take step
            weights += learning_rate * grad
            # Project onto constraint boundary [0, max_bet_exposure]
            weights = np.clip(weights, 0.0, self.max_bet_exposure)

        # Assign weights back to bets list
        results = []
        for i, bet in enumerate(bets):
            allocated_stake_fraction = float(weights[i])
            results.append({
                **bet,
                "portfolio_weight": allocated_stake_fraction,
                "allocated_stake": allocated_stake_fraction * bet.get("bankroll", 1000.0)
            })
            
        return results
