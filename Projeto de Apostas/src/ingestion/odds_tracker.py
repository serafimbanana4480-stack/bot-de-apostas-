import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


class OddsLineTracker:
    """
    Tracks and analyzes market odds, line movement, and sharp money indicators.
    Pinnacle is used as the baseline 'efficient' market maker.
    Significant line drops on Pinnacle signal smart money movement.
    Discrepancies between soft bookmakers (e.g. Bet365) and Pinnacle signal value.
    """
    def __init__(self, odds_api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.api_key = odds_api_key or "MOCK_ODDS_API_KEY"
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        # In-memory database of odds snapshots to track line movement: {match_id: [(timestamp, bookmaker, home_odds, away_odds)]}
        self.odds_history: Dict[str, List[Dict[str, Any]]] = {}

    def record_odds_snapshot(
        self, 
        match_id: str, 
        bookmaker: str, 
        home_odds: float, 
        away_odds: float,
        draw_odds: Optional[float] = None
    ) -> None:
        """Records a timestamped snapshot of odds for a match to enable trend analysis."""
        if match_id not in self.odds_history:
            self.odds_history[match_id] = []
            
        self.odds_history[match_id].append({
            "timestamp": datetime.now(),
            "bookmaker": bookmaker,
            "home_odds": home_odds,
            "away_odds": away_odds,
            "draw_odds": draw_odds
        })
        
        # Prune history older than 24 hours to manage memory
        cutoff = datetime.now() - timedelta(hours=24)
        self.odds_history[match_id] = [
            snap for snap in self.odds_history[match_id] if snap["timestamp"] >= cutoff
        ]

    def get_line_movement_2h(self, match_id: str, bookmaker: str, outcome: str = "home") -> float:
        """
        Calculates the percentage change in odds over the last 2 hours.
        A negative value indicates the odds are falling (money is coming in).
        """
        history = self.odds_history.get(match_id, [])
        if not history:
            return 0.0
            
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        
        # Filter snapshots for the target bookmaker
        bookie_snaps = [snap for snap in history if snap["bookmaker"] == bookmaker]
        if len(bookie_snaps) < 2:
            return 0.0
            
        # Get the latest snapshot and the one closest to 2 hours ago
        latest = bookie_snaps[-1]
        past_snaps = [snap for snap in bookie_snaps if snap["timestamp"] <= two_hours_ago]
        
        if not past_snaps:
            # Fallback to the oldest available snapshot
            reference = bookie_snaps[0]
        else:
            reference = past_snaps[-1]
            
        field = f"{outcome}_odds"
        latest_odds = latest.get(field, 1.0)
        past_odds = reference.get(field, 1.0)
        
        if past_odds <= 1.0 or latest_odds <= 1.0:
            return 0.0
            
        # Returns percentage change
        return (latest_odds - past_odds) / past_odds

    def detect_sharp_money_move(self, match_id: str, threshold: float = -0.03) -> Dict[str, Any]:
        """
        Analyzes line movement on Pinnacle (market maker).
        If Pinnacle odds fall by more than the threshold (e.g. -3%),
        it signals a "sharp money move" in that direction.
        """
        home_move = self.get_line_movement_2h(match_id, "pinnacle", "home")
        away_move = self.get_line_movement_2h(match_id, "pinnacle", "away")
        
        is_sharp_home = home_move <= threshold
        is_sharp_away = away_move <= threshold
        
        return {
            "sharp_move_on_home": is_sharp_home,
            "sharp_move_on_away": is_sharp_away,
            "home_pinnacle_change_2h": home_move,
            "away_pinnacle_change_2h": away_move
        }

    def fetch_live_market_odds(self, sport: str = "soccer_epl") -> List[Dict[str, Any]]:
        """
        Fetches live market odds using The Odds API.
        Extracts Pinnacle and Betfair Exchange odds along with other soft bookies.
        """
        self.logger.info(f"Fetching live market odds for {sport}...")
        if self.api_key == "MOCK_ODDS_API_KEY":
            # Return high-quality mock data structure matching the Odds API schema
            return [
                {
                    "id": "epl_match_1",
                    "sport_key": "soccer_epl",
                    "commence_time": (datetime.now() + timedelta(hours=18)).isoformat() + "Z",
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "bookmakers": [
                        {
                            "key": "pinnacle",
                            "title": "Pinnacle",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Arsenal", "price": 1.85},
                                        {"name": "Chelsea", "price": 4.10},
                                        {"name": "Draw", "price": 3.65}
                                    ]
                                }
                            ]
                        },
                        {
                            "key": "betfair_ex_eu",
                            "title": "Betfair Exchange",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Arsenal", "price": 1.87},
                                        {"name": "Chelsea", "price": 4.15},
                                        {"name": "Draw", "price": 3.70}
                                    ]
                                }
                            ]
                        },
                        {
                            "key": "bet365",
                            "title": "Bet365",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Arsenal", "price": 1.80},
                                        {"name": "Chelsea", "price": 4.30},  # Value bet compared to Pinnacle 4.10!
                                        {"name": "Draw", "price": 3.60}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]

        # Real API request
        try:
            url = f"{self.base_url}/{sport}/odds/"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,uk",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
            res = requests.get(url, params=params)
            res.raise_for_status()
            data = res.json()
            
            # Record snaps in database
            for match in data:
                m_id = match["id"]
                for bookie in match.get("bookmakers", []):
                    b_key = bookie["key"]
                    h2h_market = next((m for m in bookie.get("markets", []) if m["key"] == "h2h"), None)
                    if h2h_market:
                        outcomes = h2h_market.get("outcomes", [])
                        home_odds = next((o["price"] for o in outcomes if o["name"] == match["home_team"]), 1.0)
                        away_odds = next((o["price"] for o in outcomes if o["name"] == match["away_team"]), 1.0)
                        draw_odds = next((o["price"] for o in outcomes if o["name"] == "Draw"), None)
                        self.record_odds_snapshot(m_id, b_key, home_odds, away_odds, draw_odds)
            
            return data
        except Exception as e:
            self.logger.error(f"Error fetching live odds from API: {e}")
            return []
