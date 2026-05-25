"""
The Odds API client — FREE tier (500 requests/day).
Register at https://the-odds-api.com/

Provides live odds for upcoming matches.
Used for: live edge detection, paper trading, CLV validation.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"


class OddsAPIClient:
    """Client for The Odds API (free tier: 500 req/day)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")
        self._last_request = 0.0
        self._min_interval = 5.0  # Rate limit: ~12 req/min to stay under 500/day

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("ODDS_API_KEY not configured. Register at https://the-odds-api.com/")
            return {}
        self._throttle()
        url = f"{BASE_URL}/{path.lstrip('/')}"
        p = params or {}
        p["apiKey"] = self.api_key
        try:
            resp = requests.get(url, params=p, timeout=30)
            if resp.status_code == 429:
                logger.warning("Odds API rate limit hit — waiting 60s")
                time.sleep(60)
                return self._get(path, params)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Odds API request failed: %s", e)
            return {}

    def get_sports(self) -> List[Dict[str, str]]:
        """List available sports."""
        data = self._get("/sports")
        return data if isinstance(data, list) else []

    def get_live_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h",
        odds_format: str = "decimal",
        date_format: str = "iso",
    ) -> pd.DataFrame:
        """Alias for get_odds (live and upcoming events)."""
        return self.get_odds(sport, regions, markets, odds_format, date_format)

    def get_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h",
        odds_format: str = "decimal",
        date_format: str = "iso",
    ) -> pd.DataFrame:
        """
        Fetch current odds for a sport.

        sport keys: soccer_epl, soccer_spain_la_liga, soccer_germany_bundesliga,
                    soccer_italy_serie_a, soccer_france_ligue_one, etc.
        """
        data = self._get(
            f"/sports/{sport}/odds",
            {
                "regions": regions,
                "markets": markets,
                "oddsFormat": odds_format,
                "dateFormat": date_format,
            },
        )
        if not data:
            return pd.DataFrame()

        rows = []
        for event in data:
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence = event.get("commence_time", "")
            match_id = event.get("id", "")

            for bookmaker in event.get("bookmakers", []):
                bm_name = bookmaker.get("title", "")
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "h2h":
                        outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                        rows.append({
                            "match_id": match_id,
                            "commence_time": commence,
                            "home_team": home_team,
                            "away_team": away_team,
                            "bookmaker": bm_name,
                            "odd_home": outcomes.get(home_team),
                            "odd_away": outcomes.get(away_team),
                            "odd_draw": outcomes.get("Draw"),
                        })

        return pd.DataFrame(rows)

    def get_usage(self) -> Dict[str, Any]:
        """Check remaining quota (reads 'x-requests-remaining' header)."""
        # Trigger a lightweight request
        _ = self._get("/sports")
        # Header not directly accessible here; in practice you'd track calls locally
        return {"note": "Track requests locally; free tier = 500/day"}
