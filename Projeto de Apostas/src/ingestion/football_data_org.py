"""
football-data.org client — FREE tier (register at https://www.football-data.org/client/register).
10 requests/minute; major European competitions included at no cost.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"
MIN_REQUEST_INTERVAL = 6.0  # ~10 req/min free tier


class FootballDataOrgClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("FOOTBALL_DATA_ORG_TOKEN", "")
        self._last_request = 0.0

    def _headers(self) -> Dict[str, str]:
        return {"X-Auth-Token": self.api_token} if self.api_token else {}

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request = time.time()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_token:
            logger.warning("FOOTBALL_DATA_ORG_TOKEN not set — skipping live fetch.")
            return {}
        self._throttle()
        url = f"{BASE_URL}/{path.lstrip('/')}"
        try:
            resp = requests.get(url, headers=self._headers(), params=params or {}, timeout=30)
            if resp.status_code == 429:
                logger.warning("Rate limit — sleeping 60s")
                time.sleep(60)
                return self._get(path, params)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("football-data.org request failed: %s", e)
            return {}

    def fetch_finished_matches(
        self,
        competition_code: str = "PL",
        season: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        competition_code: PL, PD, SA, BL1, FL1, etc.
        Returns normalized DataFrame for Poisson training.
        """
        params: Dict[str, Any] = {"status": "FINISHED"}
        if season:
            params["season"] = season
        data = self._get(f"competitions/{competition_code}/matches", params)
        matches = data.get("matches", [])
        if not matches:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for m in matches:
            score = m.get("score", {}).get("fullTime", {})
            home = m.get("homeTeam", {}).get("name", "")
            away = m.get("awayTeam", {}).get("name", "")
            hg, ag = score.get("home"), score.get("away")
            if hg is None or ag is None:
                continue
            if hg > ag:
                outcome = "1"
            elif hg == ag:
                outcome = "X"
            else:
                outcome = "2"
            rows.append({
                "match_id": m.get("id"),
                "date": m.get("utcDate", "")[:10],
                "home_team": home,
                "away_team": away,
                "home_goals": int(hg),
                "away_goals": int(ag),
                "actual_outcome": outcome,
                "league": competition_code,
                "odd_1": None,
                "odd_X": None,
                "odd_2": None,
                "closing_odd": None,
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        logger.info("Fetched %s finished matches for %s", len(df), competition_code)
        return df

    def fetch_multiple_leagues(
        self,
        codes: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        codes = codes or ["PL", "PD", "SA", "BL1", "FL1"]
        frames = [self.fetch_finished_matches(c) for c in codes]
        frames = [f for f in frames if not f.empty]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
