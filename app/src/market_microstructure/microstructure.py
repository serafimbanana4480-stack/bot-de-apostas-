from typing import Any, Dict, List

import numpy as np


class MarketMicrostructureEngine:
    """
    Analyzes market order flow, odds pressure (sharp money flow), and price impact.
    Prevents entering a market after the edge has already been consumed.
    """
    def __init__(self):
        pass

    def estimate_price_impact(self, stake: float, market_liquidity: float, b_parameter: float = 0.05) -> float:
        """
        Estimates the upward/downward odds drift caused by executing a large order.
        Simple price-impact model: drift_pct = b * sqrt(stake / liquidity)
        """
        if market_liquidity <= 0 or stake <= 0:
            return 0.0
            
        ratio = stake / market_liquidity
        drift_pct = b_parameter * np.sqrt(ratio)
        return float(drift_pct)

    def detect_sharp_money_flow(
        self, 
        odds_time_series: List[float], 
        volumes: List[float], 
        time_window: int = 5
    ) -> Dict[str, Any]:
        """
        Flags sharp money flow if odds drop rapidly while betting volume rises.
        """
        if len(odds_time_series) < 2 or len(volumes) != len(odds_time_series):
            return {"sharp_flow_detected": False, "pressure": 0.0}
            
        recent_odds = odds_time_series[-time_window:]
        recent_vols = volumes[-time_window:]
        
        # Calculate log price change
        odds_change_pct = (recent_odds[-1] - recent_odds[0]) / recent_odds[0]
        total_vol = sum(recent_vols)
        
        # High volume accompanied by a significant downward movement in odds implies heavy sharp backing
        sharp_flow = (odds_change_pct < -0.015) and (total_vol > 5000.0)
        
        return {
            "sharp_flow_detected": sharp_flow,
            "odds_change_pct": float(odds_change_pct),
            "accumulated_volume": float(total_vol),
            "pressure": float(-odds_change_pct * total_vol)
        }


class LiquidityHeatmap:
    """
    Models the intraday variations in available market volume.
    Sportsbooks/Exchanges hold much deeper limits and liquidity close to kickoff.
    """
    def __init__(self):
        # Maps hours-to-kickoff bins to expected liquidity multipliers
        # Farther than 12 hours: low liquidity. Closer than 2 hours: peak liquidity.
        self.time_multipliers = {
            "far_out": 0.15,      # > 12 hours
            "mid_range": 0.50,    # 2 to 12 hours
            "kickoff_near": 1.00  # < 2 hours
        }

    def get_expected_liquidity(self, hours_to_kickoff: float, baseline_liquidity: float = 1000.0) -> float:
        """
        Adjusts baseline liquidity according to hours remaining until the event starts.
        """
        if hours_to_kickoff > 12.0:
            mult = self.time_multipliers["far_out"]
        elif hours_to_kickoff > 2.0:
            mult = self.time_multipliers["mid_range"]
        else:
            mult = self.time_multipliers["kickoff_near"]
            
        return baseline_liquidity * mult
