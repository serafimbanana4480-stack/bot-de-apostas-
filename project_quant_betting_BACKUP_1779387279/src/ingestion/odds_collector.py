"""
Odds Collector Module.
Handles fetching multi-bookmaker odds with rate limiting and exponential backoff.
Supports The Odds API with scraping fallbacks.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)

class OddsCollector:
    """Collector for multi-bookmaker odds."""
    
    def __init__(self):
        self.api_key = getattr(settings, "ODDS_API_KEY", "")
        if not self.api_key:
            raise ValueError("ODDS_API_KEY is missing. Real data collection requires an API key.")
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        self.request_count = 0
        
    async def fetch_odds(
        self, 
        sport: str, 
        regions: str = "eu,uk", 
        markets: str = "h2h,spreads"
    ) -> List[Dict[str, Any]]:
        """Fetch odds with retry logic and rate limit handling."""
        if not self.api_key:
            raise ValueError("ODDS_API_KEY is not configured.")
            
        sport_key = self._map_sport(sport)
        url = f"{self.base_url}/{sport_key}/odds"
        
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }
        
        return await self._execute_request_with_retry(url, params)
        
    async def _execute_request_with_retry(
        self, 
        url: str, 
        params: Dict[str, str], 
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Execute HTTP request with exponential backoff."""
        delay = 1.0
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    response = await client.get(url, params=params, timeout=10.0)
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limited. Waiting {delay}s before retry.")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                        
                    response.raise_for_status()
                    self.request_count += 1
                    return response.json()
                    
                except httpx.HTTPError as e:
                    logger.error(f"HTTP error on attempt {attempt+1}: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error("Max retries reached. Returning empty.")
                        return []
                    await asyncio.sleep(delay)
                    delay *= 2
                    
        return []
        
    def _map_sport(self, sport: str) -> str:
        """Map internal sport name to Odds API key."""
        mapping = {
            "NBA": "basketball_nba",
            "Football": "soccer_epl",
            "MMA": "mma_mixed_martial_arts"
        }
        return mapping.get(sport, "upcoming")
