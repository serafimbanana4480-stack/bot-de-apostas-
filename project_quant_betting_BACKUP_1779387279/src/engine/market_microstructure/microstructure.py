"""
Market Microstructure Module.
Simulates order book depth, liquidity heatmaps, and market impact.
"""
import math
from typing import Dict, Any

class MarketMicrostructure:
    """Models market liquidity and slippage."""
    
    def __init__(self):
        pass
        
    def get_liquidity_multiplier(self, time_to_kickoff_mins: float, sport: str) -> float:
        """
        Estimates liquidity based on time to kickoff.
        Liquidity generally follows an exponential curve, peaking at kickoff.
        """
        # Baseline liquidity is 10% of peak
        base_liquidity = 0.1 
        
        if time_to_kickoff_mins <= 0:
            return 1.0 # Peak liquidity at kickoff
            
        # Peak liquidity forms in the last 2 hours (120 mins)
        # Using an exponential decay function
        decay = math.exp(-time_to_kickoff_mins / 240.0) # half-life of ~4 hours
        
        return min(1.0, base_liquidity + (0.9 * decay))
        
    def estimate_slippage(self, stake: float, current_odds: float, liquidity_multiplier: float) -> float:
        """
        Estimate price slippage for a given stake.
        """
        if liquidity_multiplier <= 0.01:
            return current_odds * 0.10 # 10% slippage in completely illiquid markets
            
        # Simplified market impact model (square root law)
        # Assuming 10k EUR is the baseline depth for 1 tick movement at peak liquidity
        baseline_depth = 10000.0 * liquidity_multiplier
        
        impact_ticks = math.sqrt(stake / baseline_depth) if stake > 0 else 0
        
        # 1 tick = ~0.01 in decimal odds
        slippage_odds = impact_ticks * 0.01
        
        # Slippage reduces our odds
        expected_filled_odds = current_odds - slippage_odds
        
        return max(1.01, float(expected_filled_odds))
