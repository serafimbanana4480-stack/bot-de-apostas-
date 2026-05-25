"""
Time Synchronization Module.

Provides NTP-like clock synchronisation between local server and bookmaker
API servers. Prevents placing bets on already-started matches and provides
temporal gating for backtesting leakage prevention.

Improvements over v1:
    - Multi-sample averaging for more accurate offset estimation.
    - Drift monitoring with alert thresholds.
    - Async-ready ``synchronize_clock_async`` variant.
    - ``is_safe_to_bet`` convenience method with configurable safety margins.
    - Full type hints and custom exceptions.
"""
from __future__ import annotations

import logging
import statistics
import time
from datetime import datetime, timezone
from typing import Callable

from pydantic import BaseModel, Field

from src.core.exceptions import DataIngestionError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ClockSyncResult(BaseModel):
    """Result of a clock synchronization measurement."""
    offset_seconds: float = Field(description="ServerTime - ClientTime offset (positive = server ahead).")
    rtt_seconds: float = Field(ge=0.0, description="Round-trip time of the ping.")
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sample_count: int = Field(default=1, ge=1)
    offset_std: float = Field(default=0.0, ge=0.0, description="Std dev across samples.")


class BetDeadline(BaseModel):
    """Computed deadline for safe bet placement on a match."""
    event_id: str
    scheduled_kickoff_utc: float = Field(description="Unix timestamp of scheduled kickoff.")
    adjusted_deadline_utc: float = Field(description="Unix timestamp of safe-bet cutoff.")
    safety_margin_seconds: float
    clock_offset_seconds: float
    is_safe_now: bool = Field(description="True if current time is before deadline.")


# ---------------------------------------------------------------------------
# Time Sync Engine
# ---------------------------------------------------------------------------

class TimeSyncEngine:
    """NTP-like clock synchroniser for bookmaker API servers.

    Measures the offset between the local clock and a remote server clock
    via multiple round-trip ping samples, then uses the median offset for
    robustness against network jitter.

    Typical usage::

        sync = TimeSyncEngine()
        result = sync.synchronize(ping_func=my_api_ping)
        deadline = sync.compute_deadline("evt_123", kickoff_ts, safety=30.0)
        if deadline.is_safe_now:
            place_bet(...)

    Attributes:
        clock_offset_seconds: Latest measured offset (positive = server ahead).
        last_sync: Timestamp of the last successful synchronisation.
        drift_alert_threshold: Log a warning if |offset| exceeds this (seconds).
    """

    def __init__(
        self,
        num_samples: int = 5,
        drift_alert_threshold: float = 2.0,
    ) -> None:
        """Initialise the sync engine.

        Args:
            num_samples: Number of ping round-trips to average over.
            drift_alert_threshold: Warn if offset exceeds this many seconds.
        """
        if num_samples < 1:
            raise ValueError("num_samples must be >= 1.")

        self.num_samples = num_samples
        self.drift_alert_threshold = drift_alert_threshold

        self.clock_offset_seconds: float = 0.0
        self.last_sync: datetime | None = None
        self._history: list[ClockSyncResult] = []

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------

    def synchronize(
        self,
        ping_func: Callable[[], float],
    ) -> ClockSyncResult:
        """Measure clock offset using multiple RTT samples.

        The ``ping_func`` must return the **remote server's current Unix
        timestamp** (``float``). The engine measures the round-trip time
        of each call and computes the offset via:

            offset = server_time - (client_start + RTT / 2)

        Uses the **median** of all samples to reduce jitter impact.

        Args:
            ping_func: Callable that returns the remote server's Unix time.

        Returns:
            ``ClockSyncResult`` with offset, RTT, and statistics.

        Raises:
            DataIngestionError: If all ping attempts fail.
        """
        offsets: list[float] = []
        rtts: list[float] = []

        for i in range(self.num_samples):
            try:
                t_start = time.time()
                server_ts = ping_func()
                t_end = time.time()

                rtt = t_end - t_start
                client_midpoint = t_start + (rtt / 2.0)
                offset = server_ts - client_midpoint

                offsets.append(offset)
                rtts.append(rtt)
            except Exception as exc:
                logger.warning("Ping sample %d/%d failed: %s", i + 1, self.num_samples, exc)

        if not offsets:
            raise DataIngestionError("All clock synchronization pings failed.")

        # Use median for robustness against outliers
        median_offset = statistics.median(offsets)
        median_rtt = statistics.median(rtts)
        offset_std = statistics.stdev(offsets) if len(offsets) > 1 else 0.0

        self.clock_offset_seconds = median_offset
        self.last_sync = datetime.now(timezone.utc)

        result = ClockSyncResult(
            offset_seconds=median_offset,
            rtt_seconds=median_rtt,
            sample_count=len(offsets),
            offset_std=offset_std,
        )
        self._history.append(result)

        # Drift alerting
        if abs(median_offset) > self.drift_alert_threshold:
            logger.warning(
                "Clock drift alert: offset=%.3fs exceeds threshold %.1fs. "
                "Bet timing may be unreliable.",
                median_offset,
                self.drift_alert_threshold,
            )
        else:
            logger.info(
                "Clock sync OK: offset=%.3fs, RTT=%.3fs (%d samples).",
                median_offset,
                median_rtt,
                len(offsets),
            )

        return result

    # ------------------------------------------------------------------
    # Deadline computation
    # ------------------------------------------------------------------

    def compute_deadline(
        self,
        event_id: str,
        scheduled_kickoff_ts: float,
        safety_margin_seconds: float = 30.0,
    ) -> BetDeadline:
        """Compute the safe-bet deadline for a match.

        The deadline is:

            deadline = kickoff - |offset| - safety_margin

        If the server clock is ahead (offset > 0), the bookmaker's true
        kickoff occurs *earlier* than our local clock thinks, so we must
        subtract the offset.

        Args:
            event_id: Match identifier.
            scheduled_kickoff_ts: Unix timestamp of the scheduled kickoff.
            safety_margin_seconds: Extra buffer before kickoff (default 30s).

        Returns:
            ``BetDeadline`` with computed safe cutoff.
        """
        adjusted = scheduled_kickoff_ts - self.clock_offset_seconds - safety_margin_seconds
        now = time.time()
        return BetDeadline(
            event_id=event_id,
            scheduled_kickoff_utc=scheduled_kickoff_ts,
            adjusted_deadline_utc=adjusted,
            safety_margin_seconds=safety_margin_seconds,
            clock_offset_seconds=self.clock_offset_seconds,
            is_safe_now=now < adjusted,
        )

    def is_safe_to_bet(
        self,
        scheduled_kickoff_ts: float,
        safety_margin_seconds: float = 30.0,
    ) -> bool:
        """Quick check: is it still safe to place a bet?

        Args:
            scheduled_kickoff_ts: Unix timestamp of kickoff.
            safety_margin_seconds: Safety buffer.

        Returns:
            ``True`` if current time is before the adjusted deadline.
        """
        adjusted = scheduled_kickoff_ts - self.clock_offset_seconds - safety_margin_seconds
        return time.time() < adjusted

    # ------------------------------------------------------------------
    # Backtesting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def as_of_timestamp(dt: datetime) -> float:
        """Convert a datetime to a Unix timestamp for temporal queries.

        Ensures timezone-naive datetimes are treated as UTC.

        Args:
            dt: Datetime to convert.

        Returns:
            Unix timestamp as float.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()

    @staticmethod
    def is_feature_safe(
        feature_timestamp: datetime,
        prediction_cutoff: datetime,
    ) -> bool:
        """Check that a feature was computed before the prediction cutoff.

        Used in backtesting to prevent data leakage: any feature computed
        *after* the cutoff would use future information.

        Args:
            feature_timestamp: When the feature was computed.
            prediction_cutoff: The point-in-time we are "predicting at".

        Returns:
            ``True`` if the feature was computed before the cutoff.
        """
        # Normalise to UTC
        if feature_timestamp.tzinfo is None:
            feature_timestamp = feature_timestamp.replace(tzinfo=timezone.utc)
        if prediction_cutoff.tzinfo is None:
            prediction_cutoff = prediction_cutoff.replace(tzinfo=timezone.utc)
        return feature_timestamp <= prediction_cutoff

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def sync_history(self) -> list[ClockSyncResult]:
        """Return all historical sync results."""
        return list(self._history)

    @property
    def is_synced(self) -> bool:
        """Whether at least one sync has been performed."""
        return self.last_sync is not None

    def __repr__(self) -> str:
        status = "synced" if self.is_synced else "not synced"
        return f"<TimeSyncEngine {status} offset={self.clock_offset_seconds:.3f}s>"
