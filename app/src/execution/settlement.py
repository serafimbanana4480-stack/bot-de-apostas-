import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("settlement")

class SettlementRulesEngine:
    """
    Validates and cross-references game outcomes from multiple external APIs/sources
    to prevent faulty settlements (e.g. overtimes, abandoned matches).
    """
    def __init__(self):
        pass

    def verify_and_settle(
        self, 
        source_a_data: Dict[str, Any], 
        source_b_data: Dict[str, Any],
        sport: str = "football"
    ) -> Dict[str, Any]:
        """
        Compares results from source A and source B.
        Required data format:
        {
            "game_id": str,
            "home_score": int,
            "away_score": int,
            "status": str # "finished", "postponed", "cancelled"
        }
        """
        game_id = source_a_data.get("game_id")
        
        status_a = source_a_data.get("status")
        status_b = source_b_data.get("status")
        
        if status_a != status_b:
            logger.error(f"SETTLEMENT CONFLICT: Game {game_id} status mismatch. Source A: {status_a}, Source B: {status_b}")
            return {"settled": False, "reason": "Status mismatch conflict"}
            
        if status_a in ["postponed", "cancelled"]:
            return {"settled": True, "outcome": "VOID", "reason": f"Match was {status_a}"}

        home_a = source_a_data.get("home_score")
        home_b = source_b_data.get("home_score")
        away_a = source_a_data.get("away_score")
        away_b = source_b_data.get("away_score")
        
        if home_a != home_b or away_a != away_b:
            logger.error(f"SETTLEMENT CONFLICT: Score mismatch on {game_id}. A: {home_a}-{away_a}, B: {home_b}-{away_b}")
            return {"settled": False, "reason": "Score mismatch conflict"}

        # Settle winner
        if home_a > away_a:
            winner = "HOME"
        elif away_a > home_a:
            winner = "AWAY"
        else:
            # Draw handling by sport
            if sport.lower() in ("nba", "basketball", "mma", "ufc", "tennis"):
                # These sports do not end in draws (overtime or decision)
                winner = "HOME_OT" if home_a > away_a else "AWAY_OT"
                logger.warning(f"Unexpected tie in {sport} game {game_id} — marking as OT/decision required")
            else:
                winner = "DRAW"
            
        return {
            "settled": True,
            "outcome": "SETTLED",
            "winner": winner,
            "home_score": home_a,
            "away_score": away_a,
            "reason": "Verified cross-source parity"
        }

    def get_result(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve settled result for a match if available."""
        # This is a stub — in production this would query a result database/API
        logger.debug("get_result stub called for %s", match_id)
        return None
