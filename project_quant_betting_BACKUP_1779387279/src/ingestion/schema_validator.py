"""
Schema Validator — Pydantic v2 models for the VBQ data pipeline.

Provides validated models for:
    - Match events (scheduled + results).
    - Odds snapshots (single & multi-bookmaker).
    - Feature vectors.
    - Bet records.
    - Data quality scoring and anomaly flagging.

Improvements over v1:
    - Full model suite (Match, Odds, Feature, Bet) vs. single OddsEvent.
    - Cross-field validators (e.g. odds reciprocal sanity, score consistency).
    - Data quality scoring (0-100).
    - Anomaly flags with human-readable reasons.
    - Batch validation helpers returning valid + rejected splits.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"
    ABANDONED = "ABANDONED"


class MarketType(str, Enum):
    MONEYLINE = "MONEYLINE"
    SPREAD = "SPREAD"
    TOTALS = "TOTALS"
    H2H = "H2H"


class BetOutcome(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    PUSH = "PUSH"
    VOID = "VOID"
    PENDING = "PENDING"


# ---------------------------------------------------------------------------
# Data Quality
# ---------------------------------------------------------------------------

class AnomalyFlag(BaseModel):
    """Single anomaly detected during validation."""
    field: str
    reason: str
    severity: str = Field(default="warning", pattern=r"^(info|warning|critical)$")


class DataQualityReport(BaseModel):
    """Quality assessment of a validated record."""
    score: float = Field(default=100.0, ge=0.0, le=100.0, description="Quality score 0-100.")
    flags: list[AnomalyFlag] = Field(default_factory=list)
    is_acceptable: bool = Field(default=True, description="False if critical anomalies found.")

    def add_flag(self, field: str, reason: str, severity: str = "warning", penalty: float = 5.0) -> None:
        """Add an anomaly flag and apply a score penalty."""
        self.flags.append(AnomalyFlag(field=field, reason=reason, severity=severity))
        self.score = max(0.0, self.score - penalty)
        if severity == "critical":
            self.is_acceptable = False


# ---------------------------------------------------------------------------
# Match Schema
# ---------------------------------------------------------------------------

class MatchEvent(BaseModel):
    """Validated match event for any sport.

    Enforces:
        - Non-empty event/team IDs.
        - Scores >= 0 when present.
        - ``kickoff_utc`` is timezone-aware or assumed UTC.
    """
    event_id: str = Field(..., min_length=2, description="Unique match identifier.")
    sport: str = Field(..., min_length=2, description="Sport code (e.g. 'nba').")
    home_team: str = Field(..., min_length=1)
    away_team: str = Field(..., min_length=1)
    kickoff_utc: datetime = Field(..., description="Scheduled kickoff in UTC.")
    status: MatchStatus = Field(default=MatchStatus.SCHEDULED)
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    season: str = Field(default="", description="Season identifier, e.g. '2024-25'.")
    league: str = Field(default="", description="League or competition name.")
    venue: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("kickoff_utc", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def scores_consistent(self) -> "MatchEvent":
        """Scores must both be present or both be None."""
        if (self.home_score is None) != (self.away_score is None):
            raise ValueError("home_score and away_score must both be present or both None.")
        return self

    def quality_check(self) -> DataQualityReport:
        """Run anomaly checks specific to match events."""
        report = DataQualityReport()
        if self.home_team == self.away_team:
            report.add_flag("teams", "Home and away teams are identical.", "critical", 50.0)
        if self.kickoff_utc.year < 2000:
            report.add_flag("kickoff_utc", f"Suspiciously old date: {self.kickoff_utc}.", "warning", 10.0)
        if self.status == MatchStatus.FINISHED and self.home_score is None:
            report.add_flag("status", "FINISHED match has no scores.", "critical", 30.0)
        return report


# ---------------------------------------------------------------------------
# Odds Schema
# ---------------------------------------------------------------------------

class OddsSnapshot(BaseModel):
    """Single bookmaker odds snapshot for a match.

    Enforces:
        - Decimal odds > 1.0 and < 500.0.
        - Reasonable overround (flag if > 15%).
    """
    event_id: str = Field(..., min_length=2)
    bookmaker: str = Field(default="unknown", min_length=1)
    market: MarketType = Field(default=MarketType.MONEYLINE)
    odds_home: float = Field(..., gt=1.0, lt=500.0, description="Decimal odds for home.")
    odds_away: float = Field(..., gt=1.0, lt=500.0, description="Decimal odds for away.")
    odds_draw: float | None = Field(default=None, gt=1.0, lt=500.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spread_value: float | None = Field(default=None, description="Point spread (if applicable).")
    total_value: float | None = Field(default=None, description="Over/under line (if applicable).")

    @field_validator("odds_home", "odds_away")
    @classmethod
    def validate_odds(cls, v: float) -> float:
        if v <= 1.0:
            raise ValueError("Decimal odds must be > 1.0.")
        return round(v, 4)

    @property
    def implied_prob_home(self) -> float:
        """Raw implied probability for home (not vig-corrected)."""
        return 1.0 / self.odds_home

    @property
    def implied_prob_away(self) -> float:
        """Raw implied probability for away."""
        return 1.0 / self.odds_away

    @property
    def overround(self) -> float:
        """Total overround (vig). 0.0 = fair, > 0 = bookmaker margin."""
        total = self.implied_prob_home + self.implied_prob_away
        if self.odds_draw is not None:
            total += 1.0 / self.odds_draw
        return total - 1.0

    def quality_check(self) -> DataQualityReport:
        """Run anomaly checks on odds data."""
        report = DataQualityReport()
        overround = self.overround
        if overround > 0.15:
            report.add_flag("overround", f"Overround {overround:.2%} exceeds 15%.", "warning", 10.0)
        if overround < -0.01:
            report.add_flag("overround", f"Negative overround {overround:.2%} (arb?).", "critical", 25.0)
        if self.odds_home > 100.0 or self.odds_away > 100.0:
            report.add_flag("odds", "Odds exceed 100.0 — extreme longshot.", "warning", 5.0)
        return report


class MultiBookOdds(BaseModel):
    """Collection of odds snapshots across bookmakers for a single event."""
    event_id: str = Field(..., min_length=2)
    snapshots: list[OddsSnapshot] = Field(default_factory=list, min_length=0)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def best_home_odds(self) -> float:
        """Highest home odds across all bookmakers."""
        if not self.snapshots:
            return 0.0
        return max(s.odds_home for s in self.snapshots)

    @property
    def best_away_odds(self) -> float:
        """Highest away odds across all bookmakers."""
        if not self.snapshots:
            return 0.0
        return max(s.odds_away for s in self.snapshots)

    @property
    def consensus_home_odds(self) -> float:
        """Arithmetic mean of home odds across bookmakers."""
        if not self.snapshots:
            return 0.0
        return sum(s.odds_home for s in self.snapshots) / len(self.snapshots)

    @property
    def consensus_away_odds(self) -> float:
        """Arithmetic mean of away odds across bookmakers."""
        if not self.snapshots:
            return 0.0
        return sum(s.odds_away for s in self.snapshots) / len(self.snapshots)


# ---------------------------------------------------------------------------
# Feature Vector Schema
# ---------------------------------------------------------------------------

class FeatureVector(BaseModel):
    """Validated feature vector for a single match prediction.

    Attributes:
        event_id: Match ID the features are computed for.
        computed_at: When features were generated (for leakage tracking).
        features: Dict of feature_name -> value.
        feature_version: Semver tag of the pipeline that generated these.
    """
    event_id: str = Field(..., min_length=2)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    features: dict[str, float] = Field(..., min_length=1)
    feature_version: str = Field(default="0.1.0")
    target: float | None = Field(default=None, ge=0.0, le=1.0)

    def quality_check(self) -> DataQualityReport:
        """Flag features with NaN-like or extreme values."""
        import math

        report = DataQualityReport()
        nan_count = sum(1 for v in self.features.values() if math.isnan(v) or math.isinf(v))
        if nan_count > 0:
            report.add_flag(
                "features",
                f"{nan_count} feature(s) contain NaN/Inf.",
                "critical",
                20.0,
            )
        extreme = sum(1 for v in self.features.values() if abs(v) > 1e6)
        if extreme > 0:
            report.add_flag(
                "features",
                f"{extreme} feature(s) have |value| > 1e6.",
                "warning",
                5.0,
            )
        if len(self.features) < 10:
            report.add_flag(
                "features",
                f"Only {len(self.features)} features — expected 80+.",
                "warning",
                10.0,
            )
        return report


# ---------------------------------------------------------------------------
# Bet Record Schema
# ---------------------------------------------------------------------------

class BetRecord(BaseModel):
    """Immutable record of a placed bet.

    Captures placement odds, model edge, Kelly fraction, stake, and eventual
    outcome. Used by the ledger and CLV tracking modules.
    """
    bet_id: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=2)
    placed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bookmaker: str = Field(default="unknown")
    market: MarketType = Field(default=MarketType.MONEYLINE)
    selection: str = Field(..., min_length=1, description="'HOME', 'AWAY', 'DRAW', etc.")
    odds_at_placement: float = Field(..., gt=1.0, lt=500.0)
    stake: float = Field(..., gt=0.0)
    model_probability: float = Field(..., ge=0.0, le=1.0)
    model_edge_pct: float = Field(default=0.0, description="Edge in percentage points.")
    kelly_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    outcome: BetOutcome = Field(default=BetOutcome.PENDING)
    closing_odds: float | None = Field(default=None, gt=1.0, lt=500.0)
    pnl: float | None = Field(default=None, description="Profit/loss in currency units.")
    clv_pct: float | None = Field(default=None, description="Closing Line Value in %.")

    @property
    def is_settled(self) -> bool:
        return self.outcome not in (BetOutcome.PENDING,)

    def quality_check(self) -> DataQualityReport:
        """Validate bet record for suspicious patterns."""
        report = DataQualityReport()
        if self.model_edge_pct < 0:
            report.add_flag("model_edge_pct", "Negative edge — bet should not have been placed.", "warning", 15.0)
        if self.odds_at_placement > 50.0:
            report.add_flag("odds_at_placement", "Extreme longshot odds.", "warning", 5.0)
        if self.kelly_fraction > 0.5:
            report.add_flag("kelly_fraction", f"Kelly fraction {self.kelly_fraction:.2f} > 0.5.", "warning", 10.0)
        return report


# ---------------------------------------------------------------------------
# Batch Validation Utilities
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """Result of batch validation: valid records + rejected records with reasons."""
    valid: list[Any] = Field(default_factory=list)
    rejected: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    valid_count: int = 0
    rejected_count: int = 0
    avg_quality_score: float = 0.0


def validate_batch(
    records: list[dict[str, Any]],
    model_cls: type[BaseModel],
    min_quality: float = 50.0,
) -> ValidationResult:
    """Validate a batch of raw dicts against a Pydantic model.

    Args:
        records: List of raw dictionaries to validate.
        model_cls: Pydantic model class (e.g. ``MatchEvent``, ``OddsSnapshot``).
        min_quality: Minimum quality score to accept (records with quality
            checks that score below this are rejected).

    Returns:
        ``ValidationResult`` with valid/rejected splits.
    """
    result = ValidationResult(total=len(records))
    quality_scores: list[float] = []

    for i, raw in enumerate(records):
        try:
            instance = model_cls.model_validate(raw)
            # Run quality check if the model supports it
            if hasattr(instance, "quality_check"):
                qr: DataQualityReport = instance.quality_check()
                quality_scores.append(qr.score)
                if not qr.is_acceptable or qr.score < min_quality:
                    result.rejected.append({
                        "index": i,
                        "data": raw,
                        "reason": f"Quality score {qr.score:.1f} < {min_quality}",
                        "flags": [f.model_dump() for f in qr.flags],
                    })
                    continue
            else:
                quality_scores.append(100.0)
            result.valid.append(instance)
        except Exception as exc:
            result.rejected.append({
                "index": i,
                "data": raw,
                "reason": str(exc),
            })

    result.valid_count = len(result.valid)
    result.rejected_count = len(result.rejected)
    result.avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    return result
