import logging
from typing import Any, Dict

from src.ingestion.odds_api_client import OddsAPIClient


class LineShopper:
    """
    Compares odds across multiple bookmakers to find the best available price.
    Integrates with The Odds API to fetch real market data.
    """
    def __init__(self, use_mock: bool = False):
        self.logger = logging.getLogger(__name__)
        self.api_client = OddsAPIClient()
        self.use_mock = use_mock

    def get_best_odds(self, market_data: Dict[str, Dict[str, float]], side: str) -> Dict[str, Any]:
        """
        Finds the bookmaker offering the highest odd for a given outcome.
        
        :param market_data: dict of bookmakers and their odds. 
                            Format: {"pinnacle": {"home": 2.10, "away": 1.85}, "bet365": {"home": 2.05, "away": 1.90}}
        :param side: The outcome to bet on ("home", "draw", or "away").
        """
        best_odd = 0.0
        best_bookie = None
        
        for bookie, odds in market_data.items():
            if side in odds and odds[side] > best_odd:
                best_odd = odds[side]
                best_bookie = bookie
                
        return {
            "best_bookie": best_bookie,
            "best_odd": best_odd,
            "all_odds": {k: v.get(side) for k, v in market_data.items()}
        }

    def fetch_live_market(self, event_id: str, sport: str = "soccer_epl") -> Dict[str, Dict[str, float]]:
        """
        Fetches live market odds from The Odds API.
        Extracts Pinnacle (reference) and other soft books.
        """
        self.logger.info(f"Fetching live odds for event {event_id} (Sport: {sport})...")
        
        if self.use_mock:
            return {
                "pinnacle": {"home": 2.15, "draw": 3.40, "away": 3.60},
                "betfair": {"home": 2.18, "draw": 3.45, "away": 3.65},
                "bet365": {"home": 2.05, "draw": 3.30, "away": 3.50},
                "unibet": {"home": 2.10, "draw": 3.35, "away": 3.55}
            }
            
        try:
            # Note: A robust mapping from internal event_id to OddsAPI id is needed in production
            events = self.api_client.get_live_odds(sport=sport)
            
            # Find the target event
            target_event = next((e for e in events if e.get("id") == event_id), None)
            if not target_event:
                self.logger.warning(f"Event {event_id} not found in Odds API response.")
                return {}
                
            formatted_odds = {}
            for bookie in target_event.get("bookmakers", []):
                bookie_key = bookie["key"].lower()
                market = next((m for m in bookie.get("markets", []) if m["key"] == "h2h"), None)
                
                if market:
                    outcomes = market["outcomes"]
                    if len(outcomes) >= 2:
                        # Assuming structure: index 0 (home), index 1 (away), optional index 2 (draw)
                        formatted_odds[bookie_key] = {
                            "home": outcomes[0]["price"],
                            "away": outcomes[1]["price"]
                        }
                        if len(outcomes) == 3:
                            formatted_odds[bookie_key]["draw"] = outcomes[2]["price"]
                            
            # Ensure Pinnacle is present for efficiency reference
            if "pinnacle" not in formatted_odds:
                self.logger.warning("Pinnacle odds not available for this event. Efficiency baseline missing.")
                
            return formatted_odds
            
        except Exception as e:
            self.logger.error(f"Failed to fetch live odds: {e}")
            return {}
