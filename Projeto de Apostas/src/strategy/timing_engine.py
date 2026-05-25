from typing import Any, Dict


class StrategyTimingEngine:
    """
    Predicts the optimal time to place a bet based on pre-match drift models 
    and odds decay curves.
    """
    def __init__(self):
        pass

    def evaluate_optimal_entry_time(
        self, 
        hours_to_kickoff: float, 
        predicted_trend: str, 
        current_odds: float, 
        predicted_closing_odds: float
    ) -> Dict[str, Any]:
        """
        Recommends whether to place the bet 'IMMEDIATELY' or 'WAIT' for better odds.
        """
        # If we expect the line to shorten (odds go down), we buy IMMEDIATELY
        if predicted_trend == "SHORTEN" or current_odds > predicted_closing_odds:
            return {
                "action": "BET_NOW",
                "reason": "Odds expected to drop (shorten)",
                "expected_slippage_if_waiting": float(current_odds - predicted_closing_odds)
            }
            
        # If we expect the line to drift (odds go up), we wait
        if predicted_trend == "DRIFT" or current_odds < predicted_closing_odds:
            # But only wait if kickoff is not immediately imminent
            if hours_to_kickoff > 1.0:
                return {
                    "action": "WAIT",
                    "reason": "Odds expected to rise (drift)",
                    "expected_odds_gain": float(predicted_closing_odds - current_odds)
                }
                
        # If stable or very close to kickoff, execute now to guarantee fill
        return {
            "action": "BET_NOW",
            "reason": "Market is stable or kickoff is imminent",
            "expected_slippage_if_waiting": 0.0
        }
