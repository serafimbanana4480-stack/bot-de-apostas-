"""
API Health Dashboard — lightweight Prometheus-style health reporter.

Aggregates latency and error rates per API endpoint (Betfair, Pinnacle, OddsAPI, etc.)
and exposes a JSON/CLI report. No external web server required.

Usage:
    from src.monitoring.api_health_dashboard import APIHealthDashboard
    dash = APIHealthDashboard()
    dash.record("betfair", latency_ms=120, success=True)
    dash.record("pinnacle", latency_ms=800, success=False, error_type="TIMEOUT")
    print(dash.report())
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.monitoring.correlation_context import get_correlation_id


@dataclass
class APISample:
    api: str
    timestamp: str
    latency_ms: float
    success: bool
    error_type: str | None = None
    correlation_id: str | None = None


@dataclass
class APIHealthSummary:
    api: str
    total_calls: int
    success_count: int
    error_count: int
    error_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    last_error: str | None = None
    status: str = "HEALTHY"  # HEALTHY | DEGRADED | CRITICAL


class APIHealthDashboard:
    """
    In-memory + persistent JSONL aggregator for API health metrics.
    """

    DEGRADED_ERROR_RATE_PCT = 5.0
    CRITICAL_ERROR_RATE_PCT = 20.0
    DEGRADED_LATENCY_MS = 1000.0
    CRITICAL_LATENCY_MS = 5000.0
    MAX_SAMPLES_PER_API = 10_000

    def __init__(self, log_dir: str = "logs/api_health"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._samples: list[APISample] = []
        self._load_existing()

    def _sample_file(self) -> Path:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"samples_{today}.jsonl"

    def _load_existing(self) -> None:
        f = self._sample_file()
        if not f.exists():
            return
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._samples.append(APISample(**data))
                except (json.JSONDecodeError, TypeError):
                    continue

    def record(
        self,
        api: str,
        latency_ms: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        """Log a single API call sample."""
        sample = APISample(
            api=api,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latency_ms=float(latency_ms),
            success=bool(success),
            error_type=error_type,
            correlation_id=get_correlation_id(),
        )
        self._samples.append(sample)
        # Prune old samples per API to cap memory
        api_samples = [s for s in self._samples if s.api == api]
        if len(api_samples) > self.MAX_SAMPLES_PER_API:
            to_remove = len(api_samples) - self.MAX_SAMPLES_PER_API
            self._samples = (
                [s for s in self._samples if s.api != api]
                + api_samples[to_remove:]
            )
        with open(self._sample_file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(sample.__dict__, default=str) + "\n")

    def _percentile(self, values: list[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * p
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_vals) else f
        if f == c:
            return sorted_vals[f]
        return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)

    def report(self, window_hours: int | None = 24) -> dict[str, Any]:
        """Generate health report per API, optionally limited to recent window."""
        cutoff = None
        if window_hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        api_names = {s.api for s in self._samples}
        summaries: list[APIHealthSummary] = []
        for api in sorted(api_names):
            samples = [
                s for s in self._samples
                if s.api == api and (
                    cutoff is None
                    or datetime.fromisoformat(s.timestamp) >= cutoff
                )
            ]
            if not samples:
                continue
            total = len(samples)
            successes = sum(1 for s in samples if s.success)
            errors = total - successes
            error_rate = (errors / total) * 100.0
            latencies = [s.latency_ms for s in samples]
            avg_lat = statistics.mean(latencies)
            p95 = self._percentile(latencies, 0.95)
            p99 = self._percentile(latencies, 0.99)
            max_lat = max(latencies)
            last_err = next(
                (s.error_type for s in reversed(samples) if not s.success),
                None,
            )

            # Determine status
            if error_rate >= self.CRITICAL_ERROR_RATE_PCT or max_lat >= self.CRITICAL_LATENCY_MS:
                status = "CRITICAL"
            elif error_rate >= self.DEGRADED_ERROR_RATE_PCT or p95 >= self.DEGRADED_LATENCY_MS:
                status = "DEGRADED"
            else:
                status = "HEALTHY"

            summaries.append(APIHealthSummary(
                api=api,
                total_calls=total,
                success_count=successes,
                error_count=errors,
                error_rate_pct=round(error_rate, 2),
                avg_latency_ms=round(avg_lat, 2),
                p95_latency_ms=round(p95, 2),
                p99_latency_ms=round(p99, 2),
                max_latency_ms=round(max_lat, 2),
                last_error=last_err,
                status=status,
            ))

        critical = [s for s in summaries if s.status == "CRITICAL"]
        degraded = [s for s in summaries if s.status == "DEGRADED"]
        overall = "CRITICAL" if critical else "DEGRADED" if degraded else "HEALTHY"

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_hours": window_hours,
            "overall_status": overall,
            "apis": [s.__dict__ for s in summaries],
            "alerts": [
                f"{s.api} is {s.status} (error_rate={s.error_rate_pct}%, p95={s.p95_latency_ms}ms)"
                for s in summaries if s.status != "HEALTHY"
            ],
        }

    def print_report(self, window_hours: int | None = 24) -> None:
        r = self.report(window_hours)
        print("\n" + "=" * 60)
        print(f"  API Health Dashboard — {r['overall_status']}")
        print("=" * 60)
        for api in r["apis"]:
            if api["status"] == "HEALTHY":
                icon = "OK"
            elif api["status"] == "DEGRADED":
                icon = "WARN"
            else:
                icon = "CRIT"
            print(
                f"  [{icon}] {api['api']:<15} calls={api['total_calls']:<4} "
                f"err={api['error_rate_pct']:>5.1f}%  p95={api['p95_latency_ms']:>6.1f}ms"
            )
        if r["alerts"]:
            print("-" * 60)
            for a in r["alerts"]:
                print(f"  ! {a}")
        print("=" * 60 + "\n")
