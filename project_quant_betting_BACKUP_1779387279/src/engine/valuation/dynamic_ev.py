"""
Dynamic Expected Value (EV) Module.
Calculates temporal EV decay and break-even timing.
"""
from typing import Dict, Any
import math

class DynamicEV:
    """Models the decay of Expected Value over time."""
    
    def __init__(self):
        pass
        
    def calculate_temporal_ev(self, initial_edge_pct: float, time_to_kickoff_mins: float) -> Dict[str, float]:
        """
        Calculate the current EV accounting for temporal decay.
        Information edge decays as the market absorbs the information.
        """
        if initial_edge_pct <= 0:
            return {"current_ev_pct": 0.0, "decay_factor": 1.0}
            
        # Assuming the edge was discovered at t-24h (1440 mins)
        # The edge decays exponentially as it gets closer to kickoff
        # Half-life of edge is roughly 6 hours (360 mins)
        
        time_since_discovery = max(0, 1440.0 - time_to_kickoff_mins)
        decay_factor = math.exp(-time_since_discovery / 360.0)
        
        current_ev = initial_edge_pct * decay_factor
        
        return {
            "current_ev_pct": float(current_ev),
            "decay_factor": float(decay_factor)
        }
        
    def calculate_breakeven_time(self, edge_pct: float, min_acceptable_edge: float = 2.0) -> float:
        """
        Calculate how many minutes until the edge decays below the acceptable threshold.
        Returns minutes from NOW.
        """
        if edge_pct < min_acceptable_edge:
            return 0.0
            
        # Inverse of the decay function
        # edge_t = edge_initial * exp(-t / 360)
        # min_edge = edge_initial * exp(-t_max / 360)
        # ln(min_edge / edge_initial) = -t_max / 360
        # t_max = -360 * ln(min_edge / edge_initial)
        
        ratio = min_acceptable_edge / edge_pct
        mins_until_threshold = -360.0 * math.log(ratio)
        
        return float(mins_until_threshold)
