import logging
from typing import Any, Dict


class SharpMoneyDetector:
    """
    Detects Reverse Line Movement (RLM) and sharp money flow.
    If odds are drifting against our model or the public is heavily betting one side
    while the line moves the other way, this module blocks the bet.
    """
    def __init__(self, steam_threshold_pct: float = 0.03):
        self.logger = logging.getLogger(__name__)
        self.steam_threshold_pct = steam_threshold_pct

    def analyze_line_movement(
        self, 
        opening_odd: float, 
        current_odd: float, 
        bet_side: str
    ) -> Dict[str, Any]:
        """
        Analyzes how the odds have moved since opening.
        
        :param opening_odd: The odd when the market opened.
        :param current_odd: The odd right now.
        :param bet_side: The side the model wants to bet on.
        """
        # If odd dropped significantly, it means money is coming in on our side (Steam)
        # If odd rose significantly, it means money is coming in against us (Drift)
        movement_pct = (current_odd / opening_odd) - 1.0
        
        is_drifting_against_us = movement_pct > self.steam_threshold_pct
        is_steaming_with_us = movement_pct < -self.steam_threshold_pct
        
        status = "neutral"
        if is_drifting_against_us:
            status = "drifting"
            self.logger.warning(f"Line drifting against {bet_side}: {opening_odd} -> {current_odd}. "
                                f"Sharp money might be on the other side.")
        elif is_steaming_with_us:
            status = "steaming"
            self.logger.info(f"Line steaming with {bet_side}: {opening_odd} -> {current_odd}. "
                             f"Sharp money aligns with the model.")
                             
        return {
            "movement_pct": float(movement_pct),
            "status": status,
            "safe_to_bet": not is_drifting_against_us  # Reject bets if drifting hard
        }

    def detect_reverse_line_movement(
        self, 
        opening_odd: float, 
        current_odd: float, 
        public_bet_pct: float
    ) -> bool:
        """
        Detects RLM: When a large percentage of the public bets on one side, 
        but the line gets BETTER (odd goes up) for that side.
        This strongly implies institutional/sharp money is heavily backing the opposite side.
        
        :param public_bet_pct: The percentage of total tickets placed on this side (e.g. 0.80 for 80%).
        :return: True if RLM is detected.
        """
        movement_pct = (current_odd / opening_odd) - 1.0
        
        # If 70%+ of the public is on this side, but the odd INCREASED, that's RLM.
        if public_bet_pct > 0.70 and movement_pct > 0.02:
            self.logger.critical("Reverse Line Movement detected! Public is heavily on this side but line worsened.")
            return True
            
        return False

    def detect_score(
        self,
        event_id: str,
        odds_history: list,
        bet_side: str = "home",
    ) -> Dict[str, Any]:
        """
        Returns confidence score 0-1 from odds history snapshots.
        [{opening_odd, current_odd, ...}] or OddsIngestor rows.
        """
        if not odds_history or len(odds_history) < 2:
            return {"sharp_score": 0.5, "status": "insufficient_data", "safe_to_bet": True}

        sorted_hist = sorted(
            odds_history,
            key=lambda x: x.get("captured_at", x.get("timestamp", "")),
        )
        opening = float(sorted_hist[0].get("odds_home" if bet_side == "home" else "odds_away", sorted_hist[0].get("opening_odd", 2.0)))
        current = float(sorted_hist[-1].get("odds_home" if bet_side == "home" else "odds_away", sorted_hist[-1].get("current_odd", opening)))

        analysis = self.analyze_line_movement(opening, current, bet_side)
        movement = analysis["movement_pct"]

        if analysis["status"] == "steaming":
            score = min(1.0, 0.7 + abs(movement) * 2)
        elif analysis["status"] == "drifting":
            score = max(0.0, 0.3 - movement)
        else:
            score = 0.5

        return {
            "sharp_score": float(score),
            "status": analysis["status"],
            "safe_to_bet": analysis["safe_to_bet"],
            "movement_pct": movement,
            "event_id": event_id,
        }
