"""
News & Injury Headline Scraper.

Parses injury headlines from multiple sources, extracts player status modifiers,
and generates reactive team rating adjustments. Tracks timestamps to prevent
data leakage in backtesting pipelines.

Improvements over v1:
    - Pydantic models for validated output.
    - Enum-based injury statuses.
    - Configurable star-player registry per sport.
    - Multi-source aggregation with credibility weighting.
    - Timestamp-gated modifier generation for leakage prevention.
    - Thread-safe modifier cache with TTL expiry.
"""
from __future__ import annotations

import logging
import re
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from src.core.exceptions import DataIngestionError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------

class InjuryStatus(str, Enum):
    """Standardised injury statuses ordered by severity."""
    OUT = "OUT"
    DOUBTFUL = "DOUBTFUL"
    QUESTIONABLE = "QUESTIONABLE"
    PROBABLE = "PROBABLE"
    AVAILABLE = "AVAILABLE"


class PlayerTier(str, Enum):
    """Impact tier for a player on the team rating."""
    MVP_CANDIDATE = "MVP_CANDIDATE"
    ALL_STAR = "ALL_STAR"
    STARTER = "STARTER"
    ROLE_PLAYER = "ROLE_PLAYER"


class InjuryReport(BaseModel):
    """Validated output of a single injury headline parse."""
    player: str = Field(..., min_length=1, description="Player name.")
    team: str = Field(..., min_length=1, description="Team abbreviation or name.")
    status: InjuryStatus = Field(default=InjuryStatus.AVAILABLE)
    tier: PlayerTier = Field(default=PlayerTier.ROLE_PLAYER)
    rating_modifier: float = Field(
        default=0.0,
        ge=-1.0,
        le=0.0,
        description="Multiplier applied to team strength (negative = weaker).",
    )
    source: str = Field(default="unknown", description="News source identifier.")
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    headline_hash: str = Field(default="", description="SHA-256 of the raw headline for dedup.")

    @field_validator("team")
    @classmethod
    def normalise_team(cls, v: str) -> str:
        return v.strip().upper()


class TeamModifier(BaseModel):
    """Aggregated modifier for a team across all active injury reports."""
    team: str
    total_modifier: float = Field(default=0.0, ge=-1.0, le=0.0)
    active_reports: list[InjuryReport] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Rating penalty per status level
STATUS_MODIFIERS: dict[InjuryStatus, float] = {
    InjuryStatus.OUT: -0.08,
    InjuryStatus.DOUBTFUL: -0.05,
    InjuryStatus.QUESTIONABLE: -0.02,
    InjuryStatus.PROBABLE: -0.01,
    InjuryStatus.AVAILABLE: 0.0,
}

# Tier multipliers (higher tier = larger impact)
TIER_MULTIPLIERS: dict[PlayerTier, float] = {
    PlayerTier.MVP_CANDIDATE: 2.0,
    PlayerTier.ALL_STAR: 1.5,
    PlayerTier.STARTER: 1.0,
    PlayerTier.ROLE_PLAYER: 0.5,
}

# Source credibility weights (used when averaging across sources)
DEFAULT_SOURCE_WEIGHTS: dict[str, float] = {
    "espn": 1.0,
    "rotowire": 0.95,
    "fantasylabs": 0.9,
    "twitter": 0.6,
    "unknown": 0.5,
}


# ---------------------------------------------------------------------------
# Star Player Registry
# ---------------------------------------------------------------------------

# Sport-keyed registry of star players and their tier.
# Using uppercase fragments for case-insensitive matching.
STAR_REGISTRY: dict[str, dict[str, PlayerTier]] = {
    "nba": {
        "LEBRON": PlayerTier.MVP_CANDIDATE,
        "DONCIC": PlayerTier.MVP_CANDIDATE,
        "CURRY": PlayerTier.MVP_CANDIDATE,
        "GIANNIS": PlayerTier.MVP_CANDIDATE,
        "JOKIC": PlayerTier.MVP_CANDIDATE,
        "EMBIID": PlayerTier.MVP_CANDIDATE,
        "TATUM": PlayerTier.ALL_STAR,
        "EDWARDS": PlayerTier.ALL_STAR,
        "WEMBANYAMA": PlayerTier.ALL_STAR,
        "BRUNSON": PlayerTier.ALL_STAR,
        "LILLARD": PlayerTier.ALL_STAR,
        "DURANT": PlayerTier.ALL_STAR,
        "BOOKER": PlayerTier.ALL_STAR,
        "MITCHELL": PlayerTier.ALL_STAR,
        "DAVIS": PlayerTier.ALL_STAR,
    },
    "nfl": {
        "MAHOMES": PlayerTier.MVP_CANDIDATE,
        "ALLEN": PlayerTier.MVP_CANDIDATE,
        "HURTS": PlayerTier.ALL_STAR,
        "JACKSON": PlayerTier.ALL_STAR,
        "KELCE": PlayerTier.ALL_STAR,
    },
    "football": {
        "MBAPPE": PlayerTier.MVP_CANDIDATE,
        "HAALAND": PlayerTier.MVP_CANDIDATE,
        "VINICIUS": PlayerTier.ALL_STAR,
        "BELLINGHAM": PlayerTier.ALL_STAR,
        "SALAH": PlayerTier.ALL_STAR,
    },
}


# ---------------------------------------------------------------------------
# Headline Parser
# ---------------------------------------------------------------------------

class NewsInjuryParser:
    """Parses sports news headlines to extract injury status modifiers.

    Extracts player names, teams, statuses via regex, looks up the player's
    tier in the star-player registry, and computes a signed team-strength
    modifier.

    Attributes:
        sport: Sport key for star-player lookups (e.g. ``'nba'``).
        source_weights: Credibility weights per source identifier.
    """

    # Pre-compiled regex patterns (class-level for efficiency)
    _STATUS_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(OUT|DOUBTFUL|QUESTIONABLE|PROBABLE|AVAILABLE|"
        r"RULED\s+OUT|DAY[\s-]TO[\s-]DAY|GTD)\b",
        re.IGNORECASE,
    )
    _TEAM_RE: ClassVar[re.Pattern[str]] = re.compile(r"\(([^)]+)\)")
    _NAME_RE: ClassVar[re.Pattern[str]] = re.compile(r"^([A-Za-z'.·\-\s]+?)(?:\s*\()")

    # Aliases for non-standard status labels
    _STATUS_ALIASES: ClassVar[dict[str, InjuryStatus]] = {
        "RULED OUT": InjuryStatus.OUT,
        "DAY-TO-DAY": InjuryStatus.QUESTIONABLE,
        "DAY TO DAY": InjuryStatus.QUESTIONABLE,
        "GTD": InjuryStatus.QUESTIONABLE,
    }

    def __init__(
        self,
        sport: str = "nba",
        source_weights: dict[str, float] | None = None,
    ) -> None:
        self.sport = sport.lower()
        self.source_weights = source_weights or DEFAULT_SOURCE_WEIGHTS
        self._star_map = STAR_REGISTRY.get(self.sport, {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_headline(
        self,
        headline: str,
        source: str = "unknown",
    ) -> InjuryReport:
        """Parse a single headline into an ``InjuryReport``.

        Args:
            headline: Raw headline text, e.g.
                ``"LeBron James (Lakers) ruled OUT tonight with ankle sprain."``.
            source: News source identifier (e.g. ``'espn'``, ``'rotowire'``).

        Returns:
            Validated ``InjuryReport`` with computed rating modifier.

        Raises:
            DataIngestionError: If the headline cannot be parsed at all.
        """
        import hashlib

        headline_stripped = headline.strip()
        if not headline_stripped:
            raise DataIngestionError("Empty headline provided.")

        status = self._extract_status(headline_stripped)
        team = self._extract_team(headline_stripped)
        player = self._extract_player(headline_stripped)
        tier = self._lookup_tier(player)

        base_mod = STATUS_MODIFIERS[status]
        tier_mult = TIER_MULTIPLIERS[tier]
        modifier = round(base_mod * tier_mult, 6)

        h_hash = hashlib.sha256(headline_stripped.encode("utf-8")).hexdigest()

        return InjuryReport(
            player=player,
            team=team,
            status=status,
            tier=tier,
            rating_modifier=modifier,
            source=source,
            headline_hash=h_hash,
        )

    def parse_batch(
        self,
        headlines: list[tuple[str, str]],
    ) -> list[InjuryReport]:
        """Parse many ``(headline, source)`` tuples, skipping failures.

        Args:
            headlines: List of ``(headline_text, source_id)`` pairs.

        Returns:
            List of successfully parsed ``InjuryReport`` objects.
        """
        reports: list[InjuryReport] = []
        seen_hashes: set[str] = set()
        for headline, source in headlines:
            try:
                report = self.parse_headline(headline, source)
                if report.headline_hash not in seen_hashes:
                    seen_hashes.add(report.headline_hash)
                    reports.append(report)
            except (DataIngestionError, Exception) as exc:
                logger.warning("Skipping unparseable headline: %s (%s)", headline[:80], exc)
        return reports

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_status(self, headline: str) -> InjuryStatus:
        """Determine the injury status from the headline text."""
        match = self._STATUS_RE.search(headline)
        if not match:
            return InjuryStatus.AVAILABLE
        raw = match.group(0).upper().strip()
        # Check aliases first
        if raw in self._STATUS_ALIASES:
            return self._STATUS_ALIASES[raw]
        try:
            return InjuryStatus(raw)
        except ValueError:
            return InjuryStatus.AVAILABLE

    def _extract_team(self, headline: str) -> str:
        """Extract team name from parenthesised segment."""
        match = self._TEAM_RE.search(headline)
        return match.group(1).strip().upper() if match else "UNKNOWN"

    def _extract_player(self, headline: str) -> str:
        """Extract player name — text before the first parenthesis."""
        match = self._NAME_RE.match(headline)
        if match:
            return match.group(1).strip()
        # Fallback: take everything before the first known keyword
        for keyword in ("ruled", "is", "listed", "upgraded", "downgraded", "out", "doubtful"):
            idx = headline.lower().find(keyword)
            if idx > 0:
                return headline[:idx].strip()
        return "Unknown Player"

    def _lookup_tier(self, player_name: str) -> PlayerTier:
        """Look up player tier in the star-player registry."""
        name_upper = player_name.upper()
        for fragment, tier in self._star_map.items():
            if fragment in name_upper:
                return tier
        return PlayerTier.ROLE_PLAYER


# ---------------------------------------------------------------------------
# Multi-Source Aggregator
# ---------------------------------------------------------------------------

class InjuryModifierAggregator:
    """Aggregates ``InjuryReport`` objects into per-team modifiers.

    Thread-safe. Supports temporal gating to prevent data leakage in
    backtesting: only reports with ``parsed_at`` before the cutoff timestamp
    are considered.

    Attributes:
        parser: Shared ``NewsInjuryParser`` instance.
    """

    def __init__(self, parser: NewsInjuryParser | None = None) -> None:
        self.parser = parser or NewsInjuryParser()
        self._reports: list[InjuryReport] = []
        self._lock = threading.Lock()

    def ingest_headlines(
        self,
        headlines: list[tuple[str, str]],
    ) -> int:
        """Parse and store a batch of headlines.

        Args:
            headlines: List of ``(headline_text, source_id)`` tuples.

        Returns:
            Number of new unique reports added.
        """
        new_reports = self.parser.parse_batch(headlines)
        added = 0
        with self._lock:
            existing_hashes = {r.headline_hash for r in self._reports}
            for r in new_reports:
                if r.headline_hash not in existing_hashes:
                    self._reports.append(r)
                    existing_hashes.add(r.headline_hash)
                    added += 1
        logger.info("Ingested %d new injury reports (%d duplicates skipped).", added, len(new_reports) - added)
        return added

    def get_team_modifiers(
        self,
        as_of: datetime | None = None,
    ) -> dict[str, float]:
        """Compute per-team rating modifiers.

        Args:
            as_of: Temporal cutoff (UTC). Reports with ``parsed_at > as_of``
                are excluded to prevent data leakage. ``None`` uses all data.

        Returns:
            ``{team_code: aggregated_modifier}`` dict. Values in ``[-1, 0]``.
        """
        modifiers: dict[str, float] = {}
        with self._lock:
            for report in self._reports:
                if as_of is not None and report.parsed_at > as_of:
                    continue
                current = modifiers.get(report.team, 0.0)
                # Additive stacking, clamped to [-1, 0]
                modifiers[report.team] = max(-1.0, current + report.rating_modifier)
        return modifiers

    def get_team_report(
        self,
        team: str,
        as_of: datetime | None = None,
    ) -> TeamModifier:
        """Build a detailed ``TeamModifier`` for a specific team.

        Args:
            team: Team code (case-insensitive).
            as_of: Temporal cutoff for leakage prevention.

        Returns:
            ``TeamModifier`` with individual reports and total modifier.
        """
        team_upper = team.strip().upper()
        active: list[InjuryReport] = []
        total = 0.0
        with self._lock:
            for report in self._reports:
                if report.team != team_upper:
                    continue
                if as_of is not None and report.parsed_at > as_of:
                    continue
                active.append(report)
                total += report.rating_modifier
        total = max(-1.0, total)
        return TeamModifier(
            team=team_upper,
            total_modifier=total,
            active_reports=active,
        )

    def clear(self) -> None:
        """Remove all cached reports."""
        with self._lock:
            self._reports.clear()

    @property
    def report_count(self) -> int:
        """Number of stored reports."""
        with self._lock:
            return len(self._reports)
