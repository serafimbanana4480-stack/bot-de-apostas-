"""Pydantic schemas for API ingestion — fail fast on malformed provider JSON."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class OddsEvent(BaseModel):
    event_id: str = Field(..., min_length=2)
    odds_home: float = Field(..., gt=1.0, lt=100.0)
    odds_away: float = Field(..., gt=1.0, lt=100.0)
    timestamp: datetime

    @field_validator("odds_home", "odds_away")
    @classmethod
    def validate_odds_value(cls, value: float) -> float:
        if value <= 1.0:
            raise ValueError("Odds must be strictly greater than 1.0")
        return value


class OddsSnapshotRecord(BaseModel):
    """Normalized odds row persisted to Parquet."""
    event_id: str
    sport: str
    commence_time: datetime
    bookmaker: str
    market: str = "h2h"
    odds_home: float = Field(..., gt=1.0, lt=100.0)
    odds_away: float = Field(..., gt=1.0, lt=100.0)
    odds_draw: Optional[float] = Field(default=None, gt=1.0, lt=100.0)
    captured_at: datetime
    is_pinnacle: bool = False

    @field_validator("odds_home", "odds_away", "odds_draw")
    @classmethod
    def validate_odds(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 1.0:
            raise ValueError("Odds must be > 1.0")
        return value


class MatchResultRecord(BaseModel):
    event_id: str
    sport: str
    home_team: str
    away_team: str
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    status: str = "FINISHED"
    settled_at: datetime


def validate_odds_api_event(raw: Dict[str, Any], sport: str) -> List[OddsSnapshotRecord]:
    """Parse The-Odds-API event JSON into validated snapshot records."""
    records: List[OddsSnapshotRecord] = []
    event_id = raw.get("id") or raw.get("event_id", "")
    if not event_id:
        return records
    commence = raw.get("commence_time")
    if not commence:
        return records
    commence_dt = datetime.fromisoformat(commence.replace("Z", "+00:00")).replace(tzinfo=None)
    captured = datetime.now(timezone.utc)
    for bookmaker in raw.get("bookmakers", []):
        name = bookmaker.get("key", bookmaker.get("title", "unknown"))
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
            home_team = raw.get("home_team", "")
            away_team = raw.get("away_team", "")
            oh = outcomes.get(home_team)
            oa = outcomes.get(away_team)
            if oh is None or oa is None:
                continue
            draw_val = None
            for k, v in outcomes.items():
                if k not in (home_team, away_team):
                    draw_val = v
                    break
            records.append(
                OddsSnapshotRecord(
                    event_id=str(event_id),
                    sport=sport,
                    commence_time=commence_dt,
                    bookmaker=name,
                    odds_home=float(oh),
                    odds_away=float(oa),
                    odds_draw=float(draw_val) if draw_val else None,
                    captured_at=captured,
                    is_pinnacle=name.lower() == "pinnacle",
                )
            )
    return records
