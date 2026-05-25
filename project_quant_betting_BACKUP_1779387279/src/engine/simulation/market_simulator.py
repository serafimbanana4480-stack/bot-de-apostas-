"""
Market Simulator Module.
Simulates odds paths using Geometric Brownian Motion and injects Poisson news shocks.
"""
import numpy as np
from typing import Dict, Any, List

class MarketSimulator:
    """Stochastic simulator for sports betting markets."""
    
    def __init__(self, volatility: float = 0.05, shock_lambda: float = 0.1):
        self.volatility = volatility
        self.shock_lambda = shock_lambda # expected shocks per match
        
    def simulate_path(self, initial_odds: float, steps: int = 100) -> np.ndarray:
        """
        Simulate an odds path using a discrete Geometric Brownian Motion (GBM).
        """
        dt = 1.0 / steps
        path = np.zeros(steps)
        path[0] = initial_odds
        
        # Calculate implied prob for GBM
        initial_prob = 1.0 / initial_odds
        prob_path = np.zeros(steps)
        prob_path[0] = initial_prob
        
        for t in range(1, steps):
            # Standard GBM for probability
            dW = np.random.normal(0, np.sqrt(dt))
            
            # Add Poisson jumps (news shocks)
            jump = 0
            if np.random.poisson(self.shock_lambda * dt) > 0:
                jump_size = np.random.normal(0, 0.1) # 10% prob shock
                jump = jump_size
                
            dp = self.volatility * prob_path[t-1] * dW + jump
            new_prob = max(0.01, min(0.99, prob_path[t-1] + dp))
            prob_path[t] = new_prob
            
            # Convert back to odds
            path[t] = 1.0 / new_prob
            
        return path
        
    def simulate_execution(self, requested_odds: float, requested_stake: float, liquidity_multiplier: float) -> Dict[str, float]:
        """
        Simulate real-world friction: rejection, partial fills, latency.
        """
        # Rejection probability increases with stake and low liquidity
        rejection_prob = min(0.9, (requested_stake / 10000.0) * (1.0 / max(0.01, liquidity_multiplier)))
        
        if np.random.random() < rejection_prob:
            return {"status": "REJECTED", "filled_odds": 0.0, "filled_stake": 0.0}
            
        # Partial fill probability
        partial_fill_prob = min(0.5, rejection_prob * 1.5)
        filled_stake = requested_stake
        
        if np.random.random() < partial_fill_prob:
            filled_stake = requested_stake * np.random.uniform(0.1, 0.9)
            
        # Slippage simulation (modeled in microstructure, simplified here)
        slippage = np.random.exponential(scale=0.01) * (1.0 / max(0.01, liquidity_multiplier))
        filled_odds = max(1.01, requested_odds - slippage)
        
        return {
            "status": "FILLED" if filled_stake == requested_stake else "PARTIAL_FILL",
            "filled_odds": float(filled_odds),
            "filled_stake": float(filled_stake)
        }
