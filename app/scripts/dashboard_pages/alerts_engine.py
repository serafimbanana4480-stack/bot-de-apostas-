"""Alerts engine — threshold-based KPI monitoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    name: str
    value: float
    threshold: float
    severity: Severity
    message: str


@dataclass
class AlertThresholds:
    """Configurable thresholds for KPI alerts."""
    clv_min_pct: float = 1.0          # CLV must be > 1% for edge
    clv_break_even_pct: float = 2.565  # Break-even after costs
    max_drawdown_pct: float = 20.0     # Max drawdown % of bankroll
    min_win_rate_pct: float = 45.0     # Minimum acceptable win rate
    min_profit_factor: float = 1.1     # Profit factor below this is warning
    max_roi_decline_pct: float = 50.0  # ROI dropped > 50% from peak
    min_bets_for_confidence: int = 50  # Minimum bets for statistical significance


def evaluate_alerts(
    clv_report: dict,
    backtests: list[dict],
    daily_reports: list[dict],
    thresholds: AlertThresholds | None = None,
) -> list[Alert]:
    """Evaluate all KPI alerts against current data."""
    thresholds = thresholds or AlertThresholds()
    alerts: list[Alert] = []

    # CLV alerts
    mean_clv = clv_report.get("mean_clv_pct", 0)
    if mean_clv < thresholds.clv_break_even_pct:
        if mean_clv < thresholds.clv_min_pct:
            alerts.append(Alert(
                name="CLV Below Minimum",
                value=mean_clv,
                threshold=thresholds.clv_min_pct,
                severity=Severity.CRITICAL,
                message=f"CLV {mean_clv:.2f}% is below minimum {thresholds.clv_min_pct}% — no statistical edge",
            ))
        else:
            alerts.append(Alert(
                name="CLV Below Break-Even",
                value=mean_clv,
                threshold=thresholds.clv_break_even_pct,
                severity=Severity.WARNING,
                message=f"CLV {mean_clv:.2f}% is above threshold but below break-even {thresholds.clv_break_even_pct}% — profitable before costs, unprofitable after",
            ))
    else:
        alerts.append(Alert(
            name="CLV Above Break-Even",
            value=mean_clv,
            threshold=thresholds.clv_break_even_pct,
            severity=Severity.OK,
            message=f"CLV {mean_clv:.2f}% is above break-even {thresholds.clv_break_even_pct}% — profitable after costs",
        ))

    # Drawdown alert from latest backtest
    if backtests:
        latest = backtests[-1]
        max_dd = latest.get("max_drawdown_units", 0)
        bankroll = 1000  # default starting bankroll
        dd_pct = (max_dd / bankroll) * 100
        if dd_pct > thresholds.max_drawdown_pct:
            alerts.append(Alert(
                name="Max Drawdown Exceeded",
                value=dd_pct,
                threshold=thresholds.max_drawdown_pct,
                severity=Severity.CRITICAL,
                message=f"Drawdown {dd_pct:.1f}% exceeds {thresholds.max_drawdown_pct}% — risk too high",
            ))
        else:
            alerts.append(Alert(
                name="Drawdown OK",
                value=dd_pct,
                threshold=thresholds.max_drawdown_pct,
                severity=Severity.OK,
                message=f"Drawdown {dd_pct:.1f}% within {thresholds.max_drawdown_pct}% limit",
            ))

        # Win rate alert
        win_rate = latest.get("win_rate", 0) * 100
        if win_rate < thresholds.min_win_rate_pct:
            alerts.append(Alert(
                name="Win Rate Low",
                value=win_rate,
                threshold=thresholds.min_win_rate_pct,
                severity=Severity.WARNING,
                message=f"Win rate {win_rate:.1f}% below {thresholds.min_win_rate_pct}%",
            ))

        # Profit factor alert
        pf = latest.get("profit_factor", 0)
        if pf < thresholds.min_profit_factor:
            alerts.append(Alert(
                name="Profit Factor Low",
                value=pf,
                threshold=thresholds.min_profit_factor,
                severity=Severity.WARNING,
                message=f"Profit factor {pf:.2f} below {thresholds.min_profit_factor}",
            ))

        # Statistical confidence
        conf = latest.get("statistical_confidence", {})
        n_bets = conf.get("total_bets", 0)
        if n_bets < thresholds.min_bets_for_confidence:
            alerts.append(Alert(
                name="Insufficient Sample Size",
                value=float(n_bets),
                threshold=float(thresholds.min_bets_for_confidence),
                severity=Severity.WARNING,
                message=f"Only {n_bets} bets — need {thresholds.min_bets_for_confidence}+ for statistical significance",
            ))

    # Edge proven check
    edge_proven = clv_report.get("edge_proven", False)
    if not edge_proven:
        alerts.append(Alert(
            name="Edge Not Proven",
            value=0.0,
            threshold=1.0,
            severity=Severity.CRITICAL,
            message="Model does NOT beat closing line on average — do NOT go live",
        ))

    return alerts


def alerts_summary(alerts: list[Alert]) -> dict[str, int]:
    """Count alerts by severity."""
    counts = {"critical": 0, "warning": 0, "ok": 0}
    for a in alerts:
        counts[a.severity.value] += 1
    return counts
