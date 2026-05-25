"""
Odds Dynamics Module.
Forecasts odds movement, detects sharp money, and predicts the closing line.
"""
from typing import Dict, Any, List, Optional
import numpy as np

class OddsDynamicsModel:
    """Models the behavior of odds over time."""
    
    def __init__(self):
        # Configuration thresholds for sharp detection
        self.steam_move_threshold_pct = 0.05  # 5% move
        self.steam_time_window_mins = 15      # within 15 minutes
        
    def forecast_closing_line(
        self, 
        current_odds: float, 
        time_to_kickoff_mins: float,
        historical_moves: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Forecast the closing line based on current trajectory.
        """
        if not historical_moves or time_to_kickoff_mins < 10:
            return {"predicted_closing_odds": current_odds, "confidence": 0.9}
            
        # Logarithmic or linear extrapolation based on recent price action
        odds_values = [m.get("odds", current_odds) for m in historical_moves]
        if len(odds_values) > 1:
            recent_trend = odds_values[-1] - odds_values[0]
            # Dampen the trend as it approaches kickoff
            projected_move = recent_trend * (time_to_kickoff_mins / 1440.0) # normalized to 24h
            predicted_closing = current_odds + projected_move
        else:
            predicted_closing = current_odds
            
        # Ensure bounds (odds can't be <= 1)
        predicted_closing = max(1.01, predicted_closing)
        
        return {
            "predicted_closing_odds": float(predicted_closing),
            "confidence": min(0.9, 100.0 / (time_to_kickoff_mins + 1.0))
        }
        
    def detect_sharp_money(self, odds_history: List[Dict[str, Any]]) -> bool:
        """
        Detect 'steam moves' indicative of sharp money entering the market.
        """
        if len(odds_history) < 2:
            return False
            
        recent = odds_history[-1]
        for past in reversed(odds_history[:-1]):
            # Check if within time window
            if recent.get("timestamp") and past.get("timestamp"):
                time_diff = (recent["timestamp"] - past["timestamp"]).total_seconds() / 60.0
                if time_diff > self.steam_time_window_mins:
                    break
                    
            # Check price movement percentage
            if past.get("odds", 0) > 0:
                pct_move = abs(recent.get("odds", 0) - past["odds"]) / past["odds"]
                if pct_move >= self.steam_move_threshold_pct:
                    return True
                    
        return False
