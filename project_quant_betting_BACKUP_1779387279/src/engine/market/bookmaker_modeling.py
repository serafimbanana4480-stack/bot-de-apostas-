"""
Bookmaker Modeling Module.
Calibrates bookmaker-specific biases to calculate fair, margin-free odds.
"""
from typing import Dict, Any, List

class BookmakerModel:
    """Models specific bookmaker biases (overround, sharp reaction speed)."""
    
    def __init__(self):
        # Known profiles for major bookmakers
        self.profiles = {
            "pinnacle": {"margin": 0.025, "sharpness": 0.95, "bias_home": 0.0},
            "betfair": {"margin": 0.05, "sharpness": 0.90, "bias_home": 0.0}, # Base commission
            "bet365": {"margin": 0.055, "sharpness": 0.70, "bias_home": 0.01} # Slight home favorite bias
        }
        
    def calculate_fair_odds(self, bookmaker: str, home_odds: float, away_odds: float) -> Dict[str, float]:
        """
        Remove the bookmaker margin (vig) to find the 'fair' implied probability.
        Uses the proportional method.
        """
        implied_home = 1.0 / home_odds if home_odds > 0 else 0
        implied_away = 1.0 / away_odds if away_odds > 0 else 0
        
        overround = implied_home + implied_away
        
        if overround <= 0:
            return {"fair_home_prob": 0.0, "fair_away_prob": 0.0, "margin": 0.0}
            
        # Proportional distribution of margin
        fair_home_prob = implied_home / overround
        fair_away_prob = implied_away / overround
        
        # Apply bookmaker specific bias correction if known
        profile = self.profiles.get(bookmaker.lower())
        if profile and profile["bias_home"] != 0:
            fair_home_prob -= profile["bias_home"]
            fair_away_prob += profile["bias_home"]
            
        return {
            "fair_home_prob": float(fair_home_prob),
            "fair_away_prob": float(fair_away_prob),
            "margin": float(overround - 1.0)
        }
