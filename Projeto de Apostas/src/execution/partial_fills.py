import logging
from typing import Any, Dict, List

logger = logging.getLogger("partial_fills")

class PartialFillManager:
    """
    Manages partially filled orders. Decides whether to chase the remaining stake
    at slightly worse odds (slippage absorption) or cancel the remaining stake.
    """
    def __init__(self):
        pass

    def handle_partial_fill(
        self,
        event_id: str,
        filled_stake: float,
        filled_odds: float,
        unfilled_stake: float,
        min_acceptable_odds: float,
        available_levels: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Evaluates order book levels to fill the remaining stake.
        Returns a decision: 'CHASE' (with new target odds/stake) or 'CANCEL' (for the rest).
        """
        if unfilled_stake <= 0:
            return {"decision": "COMPLETED", "chase_stake": 0.0, "chase_odds": 0.0}

        # Calculate if chasing the remaining stake at available book levels keeps us above min_acceptable_odds
        chase_stake = 0.0
        weighted_chase_odds_sum = 0.0
        remaining_to_chase = unfilled_stake

        for level in available_levels:
            if remaining_to_chase <= 0:
                break
                
            match_size = min(remaining_to_chase, level["size"])
            chase_stake += match_size
            weighted_chase_odds_sum += match_size * level["price"]
            remaining_to_chase -= match_size

        if chase_stake == 0.0:
            return {"decision": "CANCEL", "reason": "NO_LIQUIDITY", "chase_stake": 0.0}

        avg_chase_odds = weighted_chase_odds_sum / chase_stake
        
        # Combined average odds for the entire order
        total_stake = filled_stake + chase_stake
        combined_odds = ((filled_stake * filled_odds) + weighted_chase_odds_sum) / total_stake
        
        if combined_odds >= min_acceptable_odds:
            logger.info(f"Chasing partial fill for {event_id}. Combined odds {combined_odds:.3f} >= min acceptable {min_acceptable_odds}")
            return {
                "decision": "CHASE",
                "chase_stake": chase_stake,
                "chase_odds": avg_chase_odds,
                "combined_odds": combined_odds
            }
        else:
            logger.warning(f"Cancelling remainder of order for {event_id}. Combined odds {combined_odds:.3f} below limit {min_acceptable_odds}")
            return {
                "decision": "CANCEL",
                "reason": "SLIPPAGE_EXCEEDED_MAO",
                "combined_odds": combined_odds
            }
