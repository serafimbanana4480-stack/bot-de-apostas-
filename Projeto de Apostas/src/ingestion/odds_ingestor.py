"""
Unified odds ingestion: fetch → validate (Pydantic) → persist Parquet.
Enables CLV, line movement, and honest backtesting.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.config import settings
from src.ingestion.odds_api_client import OddsAPIClient
from src.ingestion.schema_validator import validate_odds_api_event

logger = logging.getLogger(__name__)

SPORT_ODDS_API_MAP = {
    "football": "soccer_epl",
    "nba": "basketball_nba",
    "ufc": "mma_mixed_martial_arts",
    "mma": "mma_mixed_martial_arts",
}


class OddsIngestor:
    def __init__(
        self,
        data_root: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.data_root = Path(data_root or settings.DATA_DIR) / "raw" / "odds"
        self.client = OddsAPIClient(api_key=api_key)
        self._validation_errors: List[str] = []
        self.strict_validation: bool = False

    def get_odds_history(
        self,
        event_id: str,
        sport: str,
        hours: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Snapshots for an event within the last N hours (from Parquet)."""
        df = self.load_history(sport)
        if df.empty or "event_id" not in df.columns:
            return []
        sub = df[df["event_id"].astype(str) == str(event_id)].copy()
        if sub.empty:
            return []
        if "captured_at" in sub.columns:
            sub["captured_at"] = pd.to_datetime(sub["captured_at"], utc=True).dt.tz_localize(None)
            cutoff = pd.Timestamp.now() - pd.Timedelta(hours=hours)
            sub = sub[sub["captured_at"] >= cutoff]
        return sub.sort_values("captured_at").to_dict("records") if "captured_at" in sub.columns else sub.to_dict("records")

    def _persist(self, df: pd.DataFrame, sport: str, day: date) -> Path:
        out_dir = self.data_root / sport
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{day.isoformat()}.parquet"
        if path.exists():
            existing = pd.read_parquet(path)
            df = pd.concat([existing, df], ignore_index=True).drop_duplicates(
                subset=["event_id", "bookmaker", "captured_at"],
                keep="last",
            )
        df.to_parquet(path, index=False)
        logger.info("Persisted %s odds rows → %s", len(df), path)
        return path

    def ingest_live(
        self,
        sport: str,
        regions: str = "eu",
        markets: str = "h2h",
    ) -> pd.DataFrame:
        api_sport = SPORT_ODDS_API_MAP.get(sport, sport)
        raw_events = self.client.get_live_odds(sport=api_sport, regions=regions, markets=markets)
        if raw_events.empty:
            logger.warning("No odds returned for %s (check ODDS_API_KEY)", sport)
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for event in raw_events:
            try:
                for rec in validate_odds_api_event(event, sport):
                    rows.append(rec.model_dump())
            except Exception as e:
                self._validation_errors.append(str(e))
                logger.warning("Skipped invalid event: %s", e)

        if self.strict_validation and self._validation_errors:
            raise ValueError(f"Odds validation failed: {self._validation_errors[:5]}")

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        self._persist(df, sport, date.today())
        return df

    def load_history(self, sport: str, from_date: Optional[date] = None, to_date: Optional[date] = None) -> pd.DataFrame:
        sport_dir = self.data_root / sport
        if not sport_dir.exists():
            return pd.DataFrame()
        frames = []
        for f in sorted(sport_dir.glob("*.parquet")):
            d = date.fromisoformat(f.stem)
            if from_date and d < from_date:
                continue
            if to_date and d > to_date:
                continue
            frames.append(pd.read_parquet(f))
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def get_pinnacle_closing(
        self,
        event_id: str,
        sport: str,
        side: str = "home",
    ) -> Optional[float]:
        """Latest Pinnacle odd for event from persisted snapshots."""
        df = self.load_history(sport)
        if df.empty:
            return None
        pin = df[(df["event_id"] == event_id) & (df["is_pinnacle"])]
        if pin.empty:
            pin = df[df["event_id"] == event_id].sort_values("captured_at").tail(1)
        if pin.empty:
            return None
        col = f"odds_{side}"
        return float(pin.iloc[-1][col]) if col in pin.columns else None

    @property
    def validation_errors(self) -> List[str]:
        return list(self._validation_errors)
