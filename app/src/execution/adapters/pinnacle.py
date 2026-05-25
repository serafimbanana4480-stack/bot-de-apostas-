import base64
import logging
from typing import Any, Dict

logger = logging.getLogger("pinnacle_adapter")

class PinnacleAPIConnector:
    """
    Simulates a Pinnacle API client.
    Handles Base64 header authentication, dynamic market limits fetching, and straight bet execution.
    """
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.session_token = None

    def authenticate_session(self, password: str) -> bool:
        """
        Simulates generating the Base64 basic authentication header.
        Pinnacle requires client_id:password encoded.
        """
        if not password:
            logger.error("Authentication failed: password must be provided.")
            return False
            
        credentials = f"{self.client_id}:{password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self.session_token = f"Basic {encoded}"
        logger.info("Pinnacle basic auth session header generated.")
        return True

    def get_market_limits(self, event_id: str, market_type: str = "Moneyline") -> Dict[str, float]:
        """
        Returns dynamic maximum stake limits. In Pinnacle, limits change rapidly close to kickoff.
        """
        return {
            "max_stake": 750.0,
            "min_stake": 10.0
        }

    def place_bet(self, event_id: str, odds: float, stake: float, market_type: str = "Moneyline") -> Dict[str, Any]:
        """
        Submits a straight wager to Pinnacle.
        """
        if not self.session_token:
            return {"status": "REJECTED", "reason": "UNAUTHORIZED_NO_SESSION", "filled_stake": 0.0}
            
        limits = self.get_market_limits(event_id, market_type)
        
        if stake < limits["min_stake"]:
            return {"status": "REJECTED", "reason": "STAKE_BELOW_MINIMUM", "filled_stake": 0.0}
            
        if stake > limits["max_stake"]:
            # Pinnacle policy: executing the maximum allowable stake instead of rejecting outright
            executed_stake = limits["max_stake"]
            logger.warning(f"Pinnacle capped stake from {stake} to max limit {executed_stake}")
            return {
                "status": "PARTIALLY_FILLED",
                "filled_stake": executed_stake,
                "average_odds": odds,
                "unfilled_stake": stake - executed_stake,
                "reason": "CAPPED_BY_MAX_LIMIT"
            }
            
        return {
            "status": "FULLY_FILLED",
            "filled_stake": stake,
            "average_odds": odds,
            "unfilled_stake": 0.0
        }
