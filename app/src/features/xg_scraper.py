"""
xG (Expected Goals) scraper using understat.com

Uses the unofficial understat Python package or direct API calls.
Data sources:
- understat.com: xG, xGA, shots, deep completions, etc.

Installation:
    pip install understat

Note: understat package uses aiohttp. For synchronous usage, we wrap it.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class UnderstatScraper:
    """
    Scraper for understat.com xG data.

    Supports both the `understat` package and fallback to direct HTTP.
    """

    def __init__(self):
        self._session = None

    def _get_session(self):
        """Lazy init aiohttp session."""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                raise ImportError("aiohttp is required for UnderstatScraper")
        return self._session

    async def _close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _fetch_league_matches(
        self, league: str, season: int
    ) -> List[Dict[str, Any]]:
        """Fetch match list for a league/season."""
        try:
            from understat import Understat
        except ImportError:
            logger.error("understat package not installed. Run: pip install understat")
            return []

        session = self._get_session()
        understat = Understat(session)
        data = await understat.get_league_results(league, season)
        return data

    async def _fetch_match_data(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed data for a single match."""
        try:
            from understat import Understat
        except ImportError:
            logger.error("understat package not installed.")
            return {}

        session = self._get_session()
        understat = Understat(session)
        data = await understat.get_match_shots(match_id)
        return data

    def get_league_xg_stats(
        self,
        league: str,
        season: int,
    ) -> pd.DataFrame:
        """
        Synchronously fetch xG stats for all matches in a league season.

        Args:
            league: e.g. 'epl', 'la_liga', 'bundesliga', 'serie_a', 'ligue_1'
            season: e.g. 2023

        Returns:
            DataFrame with columns:
                match_id, date, home_team, away_team,
                home_xg, away_xg, home_xga, away_xga,
                home_shots, away_shots, home_deep, away_deep
        """
        try:
            data = asyncio.run(self._fetch_league_matches(league, season))
        except Exception as e:
            logger.error("Failed to fetch understat data: %s", e)
            return pd.DataFrame()

        records = []
        for match in data:
            records.append({
                "match_id": str(match.get("id")),
                "date": match.get("datetime", "").split(" ")[0],
                "home_team": match.get("h", {}).get("title", ""),
                "away_team": match.get("a", {}).get("title", ""),
                "home_xg": float(match.get("xG", {}).get("h", 0) or 0),
                "away_xg": float(match.get("xG", {}).get("a", 0) or 0),
                "home_goals": int(match.get("goals", {}).get("h", 0) or 0),
                "away_goals": int(match.get("goals", {}).get("a", 0) or 0),
                "home_shots": int(match.get("h", {}).get("shots", 0) or 0),
                "away_shots": int(match.get("a", {}).get("shots", 0) or 0),
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # xGA is just the opponent's xG
            df["home_xga"] = df["away_xg"]
            df["away_xga"] = df["home_xg"]

        asyncio.run(self._close())
        return df

    def get_team_xg_rolling(
        self,
        league: str,
        season: int,
        n_matches: int = 5,
    ) -> pd.DataFrame:
        """
        Get rolling xG/xGA averages per team.

        Returns DataFrame with:
            team, date, xg_roll, xga_roll, shots_roll
        """
        df = self.get_league_xg_stats(league, season)
        if df.empty:
            return pd.DataFrame()

        home = df[["date", "home_team", "home_xg", "home_xga", "home_shots"]].rename(
            columns={
                "home_team": "team",
                "home_xg": "xg",
                "home_xga": "xga",
                "home_shots": "shots",
            }
        )
        away = df[["date", "away_team", "away_xg", "away_xga", "away_shots"]].rename(
            columns={
                "away_team": "team",
                "away_xg": "xg",
                "away_xga": "xga",
                "away_shots": "shots",
            }
        )
        all_teams = pd.concat([home, away], ignore_index=True)
        all_teams = all_teams.sort_values(["team", "date"])

        all_teams["xg_roll"] = all_teams.groupby("team")["xg"].transform(
            lambda s: s.shift(1).rolling(n_matches, min_periods=1).mean()
        )
        all_teams["xga_roll"] = all_teams.groupby("team")["xga"].transform(
            lambda s: s.shift(1).rolling(n_matches, min_periods=1).mean()
        )
        all_teams["shots_roll"] = all_teams.groupby("team")["shots"].transform(
            lambda s: s.shift(1).rolling(n_matches, min_periods=1).mean()
        )

        return all_teams


def add_xg_features_to_matches(
    df_matches: pd.DataFrame,
    league: str,
    season: int,
    n_roll: int = 5,
) -> pd.DataFrame:
    """
    Add rolling xG/xGA features to a matches DataFrame.

    Args:
        df_matches: DataFrame with home_team, away_team, date
        league: understat league code
        season: season year
        n_roll: rolling window size

    Returns:
        Enriched DataFrame with home_xg_roll, away_xg_roll, etc.
    """
    scraper = UnderstatScraper()
    xg_df = scraper.get_team_xg_rolling(league, season, n_matches=n_roll)

    if xg_df.empty:
        logger.warning("No xG data available. Returning original DataFrame.")
        df_matches["home_xg_roll"] = 1.3
        df_matches["away_xg_roll"] = 1.1
        df_matches["home_xga_roll"] = 1.1
        df_matches["away_xga_roll"] = 1.3
        return df_matches

    df = df_matches.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Merge home team xG
    df = df.merge(
        xg_df[["team", "date", "xg_roll", "xga_roll"]].rename(
            columns={"team": "home_team", "xg_roll": "home_xg_roll", "xga_roll": "home_xga_roll"}
        ),
        on=["home_team", "date"],
        how="left",
    )

    # Merge away team xG
    df = df.merge(
        xg_df[["team", "date", "xg_roll", "xga_roll"]].rename(
            columns={"team": "away_team", "xg_roll": "away_xg_roll", "xga_roll": "away_xga_roll"}
        ),
        on=["away_team", "date"],
        how="left",
    )

    # Fill NaNs with league averages
    for col in ["home_xg_roll", "away_xg_roll", "home_xga_roll", "away_xga_roll"]:
        df[col] = df[col].fillna(df[col].median())
        df[col] = df[col].fillna(1.2)

    return df
