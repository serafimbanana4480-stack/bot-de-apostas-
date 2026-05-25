"""Fetch finished match results from free APIs for settlement."""
from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class ResultFetcher:
    def fetch_football_results(self, settle_date: date) -> List[Dict[str, Any]]:
        """football-data.org finished matches (free token)."""
        token = os.getenv("FOOTBALL_DATA_ORG_TOKEN", "")
        if not token:
            logger.info("No FOOTBALL_DATA_ORG_TOKEN — using local match store only")
            return self._from_local_store(settle_date)

        from src.ingestion.football_data_org import FootballDataOrgClient
        client = FootballDataOrgClient(token)
        results = []
        for code in ("PL", "PD", "SA"):
            df = client.fetch_finished_matches(code)
            if df.empty:
                continue
            day_df = df[df["date"].dt.date == settle_date]
            for _, row in day_df.iterrows():
                results.append({
                    "event_id": str(row.get("match_id", "")),
                    "source": "football-data.org",
                    "status": "FINISHED",
                    "home_score": int(row["home_goals"]),
                    "away_score": int(row["away_goals"]),
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                })
        if results:
            return results
        return self._from_local_store(settle_date)

    def _from_local_store(self, settle_date: date) -> List[Dict[str, Any]]:
        from src.core.config import settings
        from src.data.local_store import LocalDataStore

        store = LocalDataStore(settings.DATA_DIR)
        df = store.load_matches("football_mock")
        if df.empty:
            path = store.root / "mock_football.csv"
            if path.exists():
                df = pd.read_csv(path)
        if df.empty:
            return []
        df["date"] = pd.to_datetime(df["date"])
        day_df = df[df["date"].dt.date == settle_date]
        out = []
        for _, row in day_df.iterrows():
            out.append({
                "event_id": str(row.get("match_id", row.name)),
                "source": "local_store",
                "status": "FINISHED",
                "home_score": int(row["home_goals"]),
                "away_score": int(row["away_goals"]),
            })
        return out
