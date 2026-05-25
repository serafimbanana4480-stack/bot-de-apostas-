"""
football-data.co.uk CSV ingestion — FREE historical odds with Pinnacle closing lines.

This is the gold-standard free data source for CLV validation.
Provides match results + odds from multiple bookmakers including Pinnacle (PSCH/PSCD/PSCA).

League codes:
  E0  = Premier League (England)
  SP1 = La Liga (Spain)
  I1  = Serie A (Italy)
  D1  = Bundesliga (Germany)
  F1  = Ligue 1 (France)

Season format: YYZZ = 20YY/20ZZ season (e.g. 2324 = 2023/24)

CSV columns of interest:
  HomeTeam, AwayTeam, FTHG, FTAG, FTR
  PSH, PSD, PSA   — Pinnacle odds (opening/early)
  PSCH, PSCD, PSCA — Pinnacle closing odds (ground truth for CLV)
  B365H, B365D, B365A — Bet365 odds
  MaxH, MaxD, MaxA — Maximum odds across bookmakers
  AvgH, AvgD, AvgA — Average odds across bookmakers
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.football-data.co.uk/mmz4281"

LEAGUE_MAP = {
    "PL": "E0",   # Premier League
    "PD": "SP1",  # La Liga
    "SA": "I1",   # Serie A
    "BL1": "D1",  # Bundesliga
    "FL1": "F1",  # Ligue 1
}

# Columns we need from the CSV (subset of ~110 columns)
USEFUL_COLUMNS = [
    "Div", "Date", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR",
    "PSH", "PSD", "PSA",
    "PSCH", "PSCD", "PSCA",
    "B365H", "B365D", "B365A",
    "MaxH", "MaxD", "MaxA",
    "AvgH", "AvgD", "AvgA",
]


class FootballDataCoUkClient:
    """Downloads and parses historical CSVs from football-data.co.uk."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _csv_url(self, season: str, league_code: str) -> str:
        """Build URL: https://www.football-data.co.uk/mmz4281/2324/E0.csv"""
        return f"{BASE_URL}/{season}/{league_code}.csv"

    def _fetch_csv(self, season: str, league_code: str) -> pd.DataFrame:
        """Download a single CSV, optionally cache it."""
        cache_path = None
        if self.cache_dir:
            cache_path = self.cache_dir / f"{season}_{league_code}.csv"
            if cache_path.exists():
                logger.info("Cache hit: %s", cache_path)
                return pd.read_csv(cache_path)

        url = self._csv_url(season, league_code)
        logger.info("Fetching %s", url)
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            if cache_path:
                df.to_csv(cache_path, index=False)
            return df
        except requests.RequestException as e:
            logger.error("Failed to fetch %s: %s", url, e)
            return pd.DataFrame()

    def _normalize(self, df: pd.DataFrame, league: str) -> pd.DataFrame:
        """Convert raw CSV to our standard match schema with Pinnacle closing odds."""
        if df.empty:
            return df

        # Keep only useful columns that exist
        cols = [c for c in USEFUL_COLUMNS if c in df.columns]
        df = df[cols].copy()

        # Drop rows without result or goals
        df = df.dropna(subset=["FTHG", "FTAG", "FTR", "HomeTeam", "AwayTeam"])

        # Parse date (DD/MM/YYYY format)
        df["date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True)

        # Map outcome to our standard
        outcome_map = {"H": "1", "D": "X", "A": "2"}
        df["actual_outcome"] = df["FTR"].map(outcome_map)

        # Normalize column names to our schema
        rename = {
            "HomeTeam": "home_team",
            "AwayTeam": "away_team",
            "FTHG": "home_goals",
            "FTAG": "away_goals",
            "PSH": "pin_open_home",
            "PSD": "pin_open_draw",
            "PSA": "pin_open_away",
            "PSCH": "pin_close_home",
            "PSCD": "pin_close_draw",
            "PSCA": "pin_close_away",
            "B365H": "b365_home",
            "B365D": "b365_draw",
            "B365A": "b365_away",
            "MaxH": "max_home",
            "MaxD": "max_draw",
            "MaxA": "max_away",
            "AvgH": "avg_home",
            "AvgD": "avg_draw",
            "AvgA": "avg_away",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

        # Add league column
        df["league"] = league

        # Convert odds to float (some CSVs have non-numeric entries)
        odds_cols = [c for c in df.columns if any(
            c.startswith(p) for p in ("pin_", "b365_", "max_", "avg_")
        )]
        for col in odds_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows without Pinnacle closing odds (essential for CLV)
        df = df.dropna(subset=["pin_close_home", "pin_close_draw", "pin_close_away"])

        # Also require at least one set of opening/available odds
        # Use Pinnacle opening if available, else Bet365, else Max
        df["open_odd_home"] = df.get("pin_open_home", df.get("b365_home", df.get("max_home")))
        df["open_odd_draw"] = df.get("pin_open_draw", df.get("b365_draw", df.get("max_draw")))
        df["open_odd_away"] = df.get("pin_open_away", df.get("b365_away", df.get("max_away")))

        # For compatibility with existing model: odd_1/odd_X/odd_2 = Pinnacle opening
        df["odd_1"] = df.get("pin_open_home", df.get("b365_home"))
        df["odd_X"] = df.get("pin_open_draw", df.get("b365_draw"))
        df["odd_2"] = df.get("pin_open_away", df.get("b365_away"))

        # Closing odds for CLV
        df["closing_odd"] = df.apply(
            lambda r: r["pin_close_home"] if r["actual_outcome"] == "1"
            else (r["pin_close_draw"] if r["actual_outcome"] == "X" else r["pin_close_away"]),
            axis=1,
        )

        # Line movement
        df["line_movement_home"] = (
            (df["pin_close_home"] / df["open_odd_home"]) - 1.0
            if "open_odd_home" in df.columns else 0.0
        )

        # Select final columns
        final_cols = [
            "date", "home_team", "away_team", "home_goals", "away_goals",
            "actual_outcome", "league",
            "open_odd_home", "open_odd_draw", "open_odd_away",
            "odd_1", "odd_X", "odd_2",
            "pin_close_home", "pin_close_draw", "pin_close_away",
            "closing_odd", "line_movement_home",
        ]
        # Add optional odds columns if present
        for col in ["b365_home", "b365_draw", "b365_away",
                     "max_home", "max_draw", "max_away",
                     "avg_home", "avg_draw", "avg_away"]:
            if col in df.columns:
                final_cols.append(col)

        df = df[[c for c in final_cols if c in df.columns]].copy()
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def fetch_season(
        self,
        league: str = "PL",
        season: str = "2324",
    ) -> pd.DataFrame:
        """
        Fetch one season for one league.
        league: PL, PD, SA, BL1, FL1
        season: e.g. '2324' for 2023/24
        """
        code = LEAGUE_MAP.get(league, league)
        raw = self._fetch_csv(season, code)
        if raw.empty:
            return raw
        return self._normalize(raw, league)

    def fetch_multiple_seasons(
        self,
        leagues: Optional[List[str]] = None,
        seasons: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch multiple leagues and seasons.
        Default: 5 major leagues, last 5 seasons.
        """
        leagues = leagues or ["PL", "PD", "SA", "BL1", "FL1"]
        seasons = seasons or ["1920", "2021", "2122", "2223", "2324"]

        frames = []
        for league in leagues:
            for season in seasons:
                df = self.fetch_season(league, season)
                if not df.empty:
                    logger.info(
                        "League %s season %s: %d matches with Pinnacle closing odds",
                        league, season, len(df),
                    )
                    frames.append(df)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
