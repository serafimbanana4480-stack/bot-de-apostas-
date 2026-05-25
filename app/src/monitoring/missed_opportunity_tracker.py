"""
Missed Opportunity Tracker — records bets that were SKIPPED but would have won.

This quantifies the "cost of inaction" and helps tune decision thresholds.
At settlement time, any event_id that was logged as SKIP but ended up winning
is recorded as a missed opportunity with estimated P&L.

Usage:
    tracker = MissedOpportunityTracker()
    tracker.record_skip(event_id="e1", odds=2.1, predicted_prob=0.55, stake=50)
    # Later, after settlement:
    tracker.record_result(event_id="e1", outcome="WIN", final_odds=2.1)
    report = tracker.generate_report()
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.monitoring.correlation_context import get_correlation_id

logger = logging.getLogger("missed_opportunity")


@dataclass
class SkipRecord:
    event_id: str
    timestamp: str
    odds: float
    predicted_prob: float
    recommended_stake: float
    reason: str
    correlation_id: str | None = None


@dataclass
class MissedOpportunity:
    event_id: str
    skip_timestamp: str
    odds: float
    predicted_prob: float
    recommended_stake: float
    actual_outcome: str
    missed_pnl: float
    reason: str
    correlation_id: str | None = None


class MissedOpportunityTracker:
    """
    Tracks skipped bets and reconciles with results to find missed profit.
    """

    def __init__(self, log_dir: str = "logs/missed_opportunities"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._skips: dict[str, SkipRecord] = {}
        self._misses: list[MissedOpportunity] = []
        self._load_existing()

    def _skip_file(self) -> Path:
        return self.log_dir / "skips.jsonl"

    def _misses_file(self) -> Path:
        return self.log_dir / "missed.jsonl"

    def _load_existing(self) -> None:
        """Hydrate in-memory cache from persistent JSONL files."""
        if self._skip_file().exists():
            with open(self._skip_file(), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = SkipRecord(**json.loads(line))
                        self._skips[rec.event_id] = rec
                    except (json.JSONDecodeError, TypeError):
                        continue
        if self._misses_file().exists():
            with open(self._misses_file(), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        self._misses.append(MissedOpportunity(**json.loads(line)))
                    except (json.JSONDecodeError, TypeError):
                        continue

    def record_skip(
        self,
        event_id: str,
        odds: float,
        predicted_prob: float,
        recommended_stake: float,
        reason: str,
    ) -> None:
        """Record that a bet was skipped (NO_BET / WAIT / REJECTED)."""
        if event_id in self._skips:
            return
        rec = SkipRecord(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            odds=float(odds),
            predicted_prob=float(predicted_prob),
            recommended_stake=float(recommended_stake),
            reason=reason,
            correlation_id=get_correlation_id(),
        )
        self._skips[event_id] = rec
        with open(self._skip_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), default=str) + "\n")
        logger.info("Skip recorded for %s (reason: %s)", event_id, reason)

    def record_result(
        self, event_id: str, outcome: str, final_odds: float | None = None,
    ) -> MissedOpportunity | None:
        """
        Reconcile a settlement result against skips.
        If the event was skipped and outcome is WIN, it's a missed opportunity.
        """
        skip = self._skips.get(event_id)
        if skip is None:
            return None
        if outcome.upper() not in ("WIN", "WON", "1"):
            return None
        odds = final_odds if final_odds is not None else skip.odds
        missed_pnl = (odds - 1.0) * skip.recommended_stake
        miss = MissedOpportunity(
            event_id=event_id,
            skip_timestamp=skip.timestamp,
            odds=odds,
            predicted_prob=skip.predicted_prob,
            recommended_stake=skip.recommended_stake,
            actual_outcome=outcome,
            missed_pnl=missed_pnl,
            reason=skip.reason,
            correlation_id=skip.correlation_id,
        )
        self._misses.append(miss)
        with open(self._misses_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(miss), default=str) + "\n")
        logger.warning(
            "Missed opportunity: %s | stake=%.2f | odds=%.2f | missed_pnl=%.2f | reason=%s",
            event_id, skip.recommended_stake, odds, missed_pnl, skip.reason,
        )
        return miss

    def generate_report(self) -> dict[str, Any]:
        """Aggregate missed opportunity statistics."""
        if not self._misses:
            return {
                "total_missed": 0, "total_missed_pnl": 0.0,
                "avg_missed_pnl": 0.0, "by_reason": {},
            }

        total_pnl = sum(m.missed_pnl for m in self._misses)
        by_reason: dict[str, dict[str, Any]] = {}
        for m in self._misses:
            r = m.reason or "unknown"
            if r not in by_reason:
                by_reason[r] = {"count": 0, "missed_pnl": 0.0}
            by_reason[r]["count"] += 1
            by_reason[r]["missed_pnl"] += m.missed_pnl

        return {
            "total_missed": len(self._misses),
            "total_missed_pnl": round(total_pnl, 2),
            "avg_missed_pnl": round(total_pnl / len(self._misses), 2),
            "by_reason": {
                k: {"count": v["count"], "missed_pnl": round(v["missed_pnl"], 2)}
                for k, v in by_reason.items()
            },
            "latest": [asdict(m) for m in self._misses[-10:]],
        }

    def reset(self) -> None:
        """Clear in-memory and persistent state (useful in tests)."""
        self._skips.clear()
        self._misses.clear()
        for p in (self._skip_file(), self._misses_file()):
            if p.exists():
                p.unlink()
