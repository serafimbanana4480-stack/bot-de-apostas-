import logging
import random
import time
from typing import Any, Dict, List

# Import official endpoints
from nba_api.stats.endpoints import boxscoretraditionalv2, leaguegamefinder, playbyplayv2

logger = logging.getLogger(__name__)

# Standard headers to bypass stats.nba.com aggressive blocks
NBA_HEADERS = {
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nba.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
}

class NBAIngestionClient:
    """
    Ingestion client wrapping the stats.nba.com API endpoints.
    Provides rate limiting, custom headers, and retry logic.
    """
    def __init__(self, request_delay_min: float = 1.0, request_delay_max: float = 3.0, max_retries: int = 5):
        self.request_delay_min = request_delay_min
        self.request_delay_max = request_delay_max
        self.max_retries = max_retries
        
    def _wait(self) -> None:
        """Helper to throttle requests and avoid IP blocks."""
        delay = random.uniform(self.request_delay_min, self.request_delay_max)
        time.sleep(delay)

    def fetch_games_for_season(self, season: str, season_type: str = "Regular Season") -> List[Dict[str, Any]]:
        """
        Fetches all games played during a specific NBA season.
        season: e.g. '2023-24'
        season_type: 'Regular Season' or 'Playoffs'
        """
        logger.info(f"Fetching games list for season={season}, type={season_type}...")
        self._wait()
        
        for attempt in range(self.max_retries):
            try:
                # Custom request to inject headers dynamically into the nba_api session
                # nba_api sets global headers, but custom headers prevent blocks
                finder = leaguegamefinder.LeagueGameFinder(
                    season_nullable=season,
                    league_id_nullable="00", # NBA Core League
                    season_type_nullable=season_type,
                    headers=NBA_HEADERS,
                    timeout=30
                )
                df = finder.get_data_frames()[0]
                # Convert DataFrame to dictionary list
                games = df.to_dict(orient="records")
                logger.info(f"Successfully retrieved {len(games)} game records for season={season}.")
                return games
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed to fetch games: {e}")
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt + random.uniform(1, 3)) # Exponential backoff
        return []

    def fetch_box_score(self, game_id: str) -> Dict[str, Any]:
        """
        Fetches box score details (game level stats) for a given game_id.
        """
        logger.debug(f"Fetching box score for game_id={game_id}...")
        self._wait()
        
        for attempt in range(self.max_retries):
            try:
                box = boxscoretraditionalv2.BoxScoreTraditionalV2(
                    game_id=game_id,
                    headers=NBA_HEADERS,
                    timeout=30
                )
                data = box.get_dict()
                return data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed to fetch box score for {game_id}: {e}")
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt + random.uniform(1, 3))
        return {}

    def fetch_play_by_play(self, game_id: str) -> Dict[str, Any]:
        """
        Fetches play-by-play narrative logs for a given game_id.
        """
        logger.debug(f"Fetching play-by-play for game_id={game_id}...")
        self._wait()
        
        for attempt in range(self.max_retries):
            try:
                pbp = playbyplayv2.PlayByPlayV2(
                    game_id=game_id,
                    headers=NBA_HEADERS,
                    timeout=30
                )
                data = pbp.get_dict()
                return data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed to fetch play-by-play for {game_id}: {e}")
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt + random.uniform(1, 3))
        return {}
