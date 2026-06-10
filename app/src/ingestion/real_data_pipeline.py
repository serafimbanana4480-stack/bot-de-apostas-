"""
Real Data Pipeline — Ingestão de dados reais para o VBQ-UNIFIED.

NÃO GERA DADOS MOCK/SINTÉTICOS.
Se os dados não estiverem disponíveis, falha explicitamente.

Fontes primárias (gratuitas):
1. football-data.co.uk — odds históricas reais com Pinnacle closing
2. The Odds API — odds live (free tier: 500 req/day)
3. understat.com — xG data (scraping, não-oficial)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.ingestion.football_data_co_uk import FootballDataCoUkClient, LEAGUE_MAP
from src.ingestion.odds_api_client import OddsAPIClient

logger = logging.getLogger(__name__)

# Ligas menos eficientes (prioridade para apostas reais)
TARGET_LEAGUES = {
    "E0": "Premier League",      # eficiente, mas referência
    "E1": "Championship",        # MENOS EFICIENTE — foco
    "SP1": "La Liga",            # eficiente
    "SP2": "Segunda Division",   # MENOS EFICIENTE — foco
    "I1": "Serie A",             # eficiente
    "I2": "Serie B",             # MENOS EFICIENTE — foco
    "D1": "Bundesliga",          # eficiente
    "D2": "Bundesliga 2",        # MENOS EFICIENTE — foco
    "F1": "Ligue 1",             # eficiente
    "F2": "Ligue 2",             # MENOS EFICIENTE — foco
    "N1": "Eredivisie",          # MENOS EFICIENTE — foco
    "P1": "Primeira Liga",       # MENOS EFICIENTE — foco
}


class RealDataPipeline:
    """
    Pipeline de ingestão de dados reais.
    Nunca gera dados sintéticos.
    """

    def __init__(
        self,
        cache_dir: str = "data/cache/football_data_co_uk",
        output_dir: str = "data/bronze",
    ):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fd_client = FootballDataCoUkClient(cache_dir=cache_dir)
        self.odds_client = OddsAPIClient()

    def fetch_historical_season(
        self,
        season: str,
        leagues: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical data for a season from football-data.co.uk.

        Args:
            season: Season code e.g. "2324" for 2023/24
            leagues: List of league codes (e.g. ["E0", "E1", "D2"]).
                     Default: all TARGET_LEAGUES.

        Returns:
            DataFrame with standardized columns.
        """
        if leagues is None:
            leagues = list(TARGET_LEAGUES.keys())

        all_frames = []
        for league in leagues:
            try:
                df = self.fd_client.fetch_season(league, season)
                if df.empty:
                    logger.warning("No data for %s %s", league, season)
                    continue
                df = self._standardize_football_data_co_uk(df, league)
                all_frames.append(df)
                logger.info("Fetched %d matches for %s %s", len(df), league, season)
            except Exception as e:
                logger.error("Failed to fetch %s %s: %s", league, season, e)

        if not all_frames:
            raise RuntimeError(
                f"NO REAL DATA AVAILABLE for season {season}. "
                "Check internet connection and football-data.co.uk availability. "
                "This system does NOT generate mock data."
            )

        combined = pd.concat(all_frames, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"], dayfirst=True, errors="coerce")
        combined = combined.dropna(subset=["date", "home_team", "away_team"])
        return combined.sort_values("date").reset_index(drop=True)

    def fetch_live_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
    ) -> pd.DataFrame:
        """Fetch live odds from The Odds API."""
        if not self.odds_client.api_key:
            logger.warning("ODDS_API_KEY not set — live odds unavailable")
            return pd.DataFrame()
        return self.odds_client.get_odds(sport=sport, regions=regions)

    def build_training_dataset(
        self,
        seasons: List[str],
        leagues: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Build a complete training dataset across multiple seasons.

        Args:
            seasons: List of season codes e.g. ["2122", "2223", "2324"]
            leagues: League codes to include
        """
        frames = []
        for season in seasons:
            df = self.fetch_historical_season(season, leagues)
            frames.append(df)

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values("date").reset_index(drop=True)

        # Save
        output_path = self.output_dir / "matches_football_real.parquet"
        combined.to_parquet(output_path, index=False)
        logger.info("Saved real training data to %s (%d matches)", output_path, len(combined))

        return combined

    def _standardize_football_data_co_uk(
        self, df: pd.DataFrame, league_code: str
    ) -> pd.DataFrame:
        """Standardize football-data.co.uk columns to project schema."""
        rename = {
            "Date": "date",
            "HomeTeam": "home_team",
            "AwayTeam": "away_team",
            "FTHG": "home_goals",
            "FTAG": "away_goals",
            "FTR": "actual_outcome",
            # Pinnacle opening
            "PSH": "pin_open_home",
            "PSD": "pin_open_draw",
            "PSA": "pin_open_away",
            # Pinnacle closing
            "PSCH": "pin_close_home",
            "PSCD": "pin_close_draw",
            "PSCA": "pin_close_away",
            # Bet365
            "B365H": "b365_home",
            "B365D": "b365_draw",
            "B365A": "b365_away",
            # Max/Avg
            "MaxH": "max_home",
            "MaxD": "max_draw",
            "MaxA": "max_away",
            "AvgH": "avg_home",
            "AvgD": "avg_draw",
            "AvgA": "avg_away",
        }

        result = pd.DataFrame()
        for old, new in rename.items():
            if old in df.columns:
                result[new] = df[old]

        # Map result letters to 1/X/2
        if "actual_outcome" in result.columns:
            result["actual_outcome"] = result["actual_outcome"].map(
                {"H": "1", "D": "X", "A": "2"}
            )

        # Derive opening odds (use Pinnacle opening if available, else Bet365, else avg)
        for outcome, pin_open, b365, avg in [
            ("1", "pin_open_home", "b365_home", "avg_home"),
            ("X", "pin_open_draw", "b365_draw", "avg_draw"),
            ("2", "pin_open_away", "b365_away", "avg_away"),
        ]:
            col = f"open_odd_{outcome.lower().replace('1', 'home').replace('x', 'draw').replace('2', 'away')}"
            if pin_open in result.columns:
                result[col] = result[pin_open]
            elif b365 in result.columns:
                result[col] = result[b365]
            elif avg in result.columns:
                result[col] = result[avg]

        # Current odds = closing Pinnacle if available
        for outcome, pin_close in [
            ("1", "pin_close_home"),
            ("X", "pin_close_draw"),
            ("2", "pin_close_away"),
        ]:
            col = f"odd_{outcome}"
            if pin_close in result.columns:
                result[col] = result[pin_close]

        # League name
        result["league"] = TARGET_LEAGUES.get(league_code, league_code)

        # Line movement (proxy)
        if "open_odd_home" in result.columns and "pin_close_home" in result.columns:
            result["line_movement_home"] = (
                result["open_odd_home"] - result["pin_close_home"]
            ) / result["open_odd_home"]

        # Match ID
        result["match_id"] = (
            result["date"].astype(str) + "_" +
            result["home_team"].str.replace(" ", "_") + "_" +
            result["away_team"].str.replace(" ", "_")
        )

        return result


def ensure_real_data_exists(data_dir: str = "data/bronze") -> Path:
    """
    Verify that real data exists. Raises if not.

    Returns path to real data parquet.
    """
    path = Path(data_dir) / "matches_football_real.parquet"
    if path.exists():
        return path

    # Check for legacy names
    for legacy in ["matches_football_backtest.parquet", "matches_football_mock.parquet"]:
        legacy_path = Path(data_dir) / legacy
        if legacy_path.exists():
            raise RuntimeError(
                f"MOCK DATA DETECTED: {legacy_path}. "
                "This system does not allow mock data for real-money execution. "
                "Run: py scripts/ingest_real_data.py to fetch real historical data."
            )

    raise RuntimeError(
        f"NO REAL DATA FOUND at {path}. "
        "Run: py scripts/ingest_real_data.py --seasons 2122 2223 2324"
    )
