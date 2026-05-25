from typing import Any, Dict


class MarketRegimeDetector:
    """
    Identifies NBA specific regimes (playoffs, rest fatigue B2B, local home court)
    and produces quantitative adjustment parameters.
    """
    def __init__(self):
        pass

    def detect_regime(self, game_context: Dict[str, Any]) -> str:
        """
        Categorizes the current game into a specific regime.
        """
        is_playoffs = game_context.get("is_playoffs", False)
        rest_diff = game_context.get("rest_diff", 0.0)
        
        if is_playoffs:
            return "PLAYOFFS"
        elif rest_diff <= -1.0:
            return "B2B_FATIGUE"
        elif rest_diff >= 1.0:
            return "REST_ADVANTAGE"
        else:
            return "STANDARD"

    def get_regime_modifier(self, regime: str, raw_probability: float) -> float:
        """
        Applies empirical calibration modifiers based on the detected regime.
        Prevents overestimating fatigued away teams.
        """
        if regime == "B2B_FATIGUE":
            # Penalize team probability by 3% for fatigue
            return max(0.01, min(0.99, raw_probability - 0.03))
        elif regime == "PLAYOFFS":
            # In playoffs, lean slightly more (1.5%) towards favorites (lower variance regime)
            if raw_probability > 0.50:
                return min(0.99, raw_probability + 0.015)
            else:
                return max(0.01, raw_probability - 0.015)
        elif regime == "REST_ADVANTAGE":
            # Add 2% benefit for rested team
            return min(0.99, raw_probability + 0.02)
        return raw_probability
