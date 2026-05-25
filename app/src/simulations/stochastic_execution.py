from typing import Any, Dict

import numpy as np


class StochasticExecutionSimulator:
    """
    Simulates real-world execution constraints stochastically:
    1. Sigmoid-based order rejection probability based on stake/liquidity ratio.
    2. Random slippage incorporating market volatility and price impact.
    3. Partial fill distributions using a Beta-distribution proxy.
    """
    def __init__(
        self, 
        base_slippage: float = 0.005, 
        market_volatility: float = 0.02, 
        impact_coefficient: float = 0.05
    ):
        self.base_slippage = base_slippage
        self.market_volatility = market_volatility
        self.impact_coefficient = impact_coefficient

    def simulate_slippage(self, requested_odds: float, stake: float, liquidity: float) -> float:
        """
        Calculates executed odds after applying stochastic price impact and volatility noise.
        """
        ratio = stake / max(1.0, liquidity)
        impact = self.impact_coefficient * np.sqrt(ratio)
        noise = np.random.normal(0.0, self.market_volatility)
        
        total_slippage = self.base_slippage + impact + noise
        # Make sure execution odds are at least 1.01
        executed_odds = max(1.01, requested_odds * (1.0 - total_slippage))
        return float(executed_odds)

    def calculate_rejection_probability(self, stake: float, liquidity: float) -> float:
        """
        Computes rejection probability using a sigmoid function:
        P(Reject) = 1 / (1 + exp(-k * (ratio - theta)))
        """
        ratio = stake / max(1.0, liquidity)
        # Parameters for sigmoid: k (steepness) = 10, theta (midpoint) = 0.7
        p_reject = 1.0 / (1.0 + np.exp(-10.0 * (ratio - 0.7)))
        return float(p_reject)

    def simulate_order_execution(self, requested_odds: float, stake: float, liquidity: float) -> Dict[str, Any]:
        """
        Executes stochastic roll to determine order status, slippage, and filled size.
        """
        p_reject = self.calculate_rejection_probability(stake, liquidity)
        
        # Stochastic rejection check
        if np.random.uniform(0.0, 1.0) < p_reject:
            return {
                "status": "REJECTED",
                "filled_stake": 0.0,
                "executed_odds": 1.0,
                "rejection_prob": p_reject
            }
            
        # Determine if partial fill is triggered (e.g. if stake > 80% of top-of-book depth)
        ratio = stake / max(1.0, liquidity)
        if ratio > 0.8:
            # Filled fraction sampled from Beta(5, 2) to simulate left-skewed partial fills
            filled_fraction = np.random.beta(5.0, 2.0)
            filled_stake = stake * filled_fraction
            status = "PARTIAL"
        else:
            filled_stake = stake
            status = "FILLED"
            
        executed_odds = self.simulate_slippage(requested_odds, filled_stake, liquidity)
        
        return {
            "status": status,
            "filled_stake": float(filled_stake),
            "executed_odds": executed_odds,
            "rejection_prob": p_reject
        }
