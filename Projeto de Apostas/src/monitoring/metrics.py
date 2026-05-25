"""
Prometheus metrics instrumentation for the VBQ betting system.

Defines all gauges, counters, and histograms that are exported via /metrics
and consumed by Grafana dashboards and Prometheus alert rules.
"""
from __future__ import annotations

import logging

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger("metrics")

# Use a custom registry to avoid conflicts with other prometheus users
REGISTRY = CollectorRegistry()

# ---------------------------------------------------------------------------
# Bet execution metrics
# ---------------------------------------------------------------------------
BETS_PLACED = Counter(
    "vbq_bets_placed_total",
    "Total number of bets placed",
    ["sport", "bookmaker", "side"],
    registry=REGISTRY,
)

BETS_WON = Counter(
    "vbq_bets_won_total",
    "Total number of bets won",
    ["sport", "bookmaker"],
    registry=REGISTRY,
)

BETS_REJECTED = Counter(
    "vbq_bets_rejected_total",
    "Total number of bets rejected by bookmaker",
    ["sport", "bookmaker", "reason"],
    registry=REGISTRY,
)

BETS_PARTIALLY_FILLED = Counter(
    "vbq_bets_partially_filled_total",
    "Total number of bets partially filled",
    ["sport", "bookmaker"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Financial metrics
# ---------------------------------------------------------------------------
BANKROLL_EUR = Gauge(
    "vbq_bankroll_eur",
    "Current bankroll in EUR",
    ["mode"],  # mode: paper, live
    registry=REGISTRY,
)

ROI_DAILY = Gauge(
    "vbq_roi_daily",
    "Daily return on investment",
    ["sport"],
    registry=REGISTRY,
)

CLV_AVERAGE = Gauge(
    "vbq_clv_average",
    "Average Closing Line Value percentage",
    ["sport"],
    registry=REGISTRY,
)

DRAWDOWN_PCT = Gauge(
    "vbq_drawdown_pct",
    "Current drawdown percentage from peak",
    registry=REGISTRY,
)

COMMISSION_PAID_EUR = Counter(
    "vbq_commission_paid_eur_total",
    "Total commission paid in EUR",
    ["bookmaker"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Execution metrics
# ---------------------------------------------------------------------------
EXECUTION_LATENCY_MS = Histogram(
    "vbq_execution_latency_ms",
    "Bet execution latency in milliseconds",
    ["bookmaker"],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    registry=REGISTRY,
)

API_REQUEST_LATENCY_MS = Histogram(
    "vbq_api_request_latency_ms",
    "External API request latency in milliseconds",
    ["api"],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000],
    registry=REGISTRY,
)

API_ERRORS = Counter(
    "vbq_api_errors_total",
    "Total API errors",
    ["api", "error_type"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Model / MLOps metrics
# ---------------------------------------------------------------------------
DRIFT_PSI = Gauge(
    "vbq_drift_psi",
    "Population Stability Index for feature drift",
    ["feature"],
    registry=REGISTRY,
)

MODEL_COLLAPSE_ENTROPY = Gauge(
    "vbq_model_collapse_entropy",
    "Shannon entropy of model predictions (low = collapse)",
    ["sport"],
    registry=REGISTRY,
)

CIRCUIT_BREAKER_ACTIVE = Gauge(
    "vbq_circuit_breaker_active",
    "Whether circuit breaker is currently active (1=yes, 0=no)",
    ["type"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Data ingestion metrics
# ---------------------------------------------------------------------------
ODDS_INGESTED = Counter(
    "vbq_odds_ingested_total",
    "Total odds snapshots ingested",
    ["sport", "source"],
    registry=REGISTRY,
)

DATA_STALE = Gauge(
    "vbq_data_stale_seconds",
    "Seconds since last successful data refresh",
    ["source"],
    registry=REGISTRY,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def record_bet_placed(sport: str, bookmaker: str, side: str, stake: float) -> None:
    """Record a bet placement."""
    BETS_PLACED.labels(sport=sport, bookmaker=bookmaker, side=side).inc()
    logger.info("Metric: bet placed sport=%s bookie=%s side=%s stake=%.2f", sport, bookmaker, side, stake)


def record_bet_result(sport: str, bookmaker: str, won: bool, pnl: float, commission: float = 0.0) -> None:
    """Record a bet result (win/loss)."""
    if won:
        BETS_WON.labels(sport=sport, bookmaker=bookmaker).inc()
    if commission > 0:
        COMMISSION_PAID_EUR.labels(bookmaker=bookmaker).inc(commission)


def record_bet_rejected(sport: str, bookmaker: str, reason: str) -> None:
    """Record a bet rejection."""
    BETS_REJECTED.labels(sport=sport, bookmaker=bookmaker, reason=reason).inc()


def record_execution_latency(bookmaker: str, latency_ms: float) -> None:
    """Record execution latency."""
    EXECUTION_LATENCY_MS.labels(bookmaker=bookmaker).observe(latency_ms)


def record_api_latency(api: str, latency_ms: float) -> None:
    """Record API request latency."""
    API_REQUEST_LATENCY_MS.labels(api=api).observe(latency_ms)


def record_api_error(api: str, error_type: str) -> None:
    """Record an API error."""
    API_ERRORS.labels(api=api, error_type=error_type).inc()


def update_bankroll(mode: str, amount: float) -> None:
    """Update current bankroll gauge."""
    BANKROLL_EUR.labels(mode=mode).set(amount)


def update_clv(sport: str, clv_pct: float) -> None:
    """Update average CLV gauge."""
    CLV_AVERAGE.labels(sport=sport).set(clv_pct)


def update_drawdown(pct: float) -> None:
    """Update drawdown percentage gauge."""
    DRAWDOWN_PCT.set(pct)


def update_drift_psi(feature: str, psi: float) -> None:
    """Update drift PSI gauge for a feature."""
    DRIFT_PSI.labels(feature=feature).set(psi)


def update_circuit_breaker(breaker_type: str, active: bool) -> None:
    """Update circuit breaker status gauge."""
    CIRCUIT_BREAKER_ACTIVE.labels(type=breaker_type).set(1 if active else 0)


def update_data_staleness(source: str, seconds: float) -> None:
    """Update data staleness gauge."""
    DATA_STALE.labels(source=source).set(seconds)
