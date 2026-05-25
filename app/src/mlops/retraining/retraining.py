import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("retraining")


@dataclass
class RetrainingAlert:
    triggered: bool
    reason: str
    metric: str
    value: float
    threshold: float


class RetrainingTrigger:
    """
    Evaluates drift metrics and performance indicators to trigger retraining.
    Integrates with vbq_doctor for health-check style CLV monitoring.
    """
    def __init__(
        self,
        drift_threshold: float = 0.20,
        brier_decline_tolerance: float = 0.02,
        clv_warning_threshold: float = 0.5,   # Alert when CLV < 0.5%
        clv_critical_threshold: float = 0.0,  # Trigger retrain when CLV < 0%
    ):
        self.drift_threshold = drift_threshold
        self.brier_decline_tolerance = brier_decline_tolerance
        self.clv_warning_threshold = clv_warning_threshold
        self.clv_critical_threshold = clv_critical_threshold

    def evaluate(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
    ) -> List[RetrainingAlert]:
        """Evaluate all thresholds and return a list of alerts (may be empty)."""
        alerts: List[RetrainingAlert] = []

        # 1. Drift
        psi = current_metrics.get("psi", 0.0)
        if psi > self.drift_threshold:
            alerts.append(RetrainingAlert(
                True,
                f"PSI drift {psi:.4f} > {self.drift_threshold}",
                "psi", psi, self.drift_threshold,
            ))

        # 2. Brier degradation
        current_brier = current_metrics.get("brier", 0.0)
        baseline_brier = baseline_metrics.get("brier", 0.0)
        if current_brier > (baseline_brier + self.brier_decline_tolerance):
            alerts.append(RetrainingAlert(
                True,
                f"Brier degraded {current_brier:.4f} > baseline {baseline_brier:.4f} + tol",
                "brier", current_brier, baseline_brier + self.brier_decline_tolerance,
            ))

        # 3. ECE
        current_ece = current_metrics.get("ece", 0.0)
        if current_ece > 0.08:
            alerts.append(RetrainingAlert(
                True, f"ECE {current_ece:.4f} > 0.08",
                "ece", current_ece, 0.08,
            ))

        # 4. CLV critical (triggers retraining)
        avg_clv = current_metrics.get("avg_clv_pct", 0.0)
        if avg_clv < self.clv_critical_threshold:
            alerts.append(RetrainingAlert(
                True,
                f"CLV critical {avg_clv:.2f}% < {self.clv_critical_threshold}%",
                "avg_clv_pct", avg_clv, self.clv_critical_threshold,
            ))
        elif avg_clv < self.clv_warning_threshold:
            alerts.append(RetrainingAlert(
                False,
                f"CLV warning {avg_clv:.2f}% < {self.clv_warning_threshold}%",
                "avg_clv_pct", avg_clv, self.clv_warning_threshold,
            ))

        return alerts

    def should_retrain(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
    ) -> bool:
        """Legacy bool interface. True if any critical alert fires."""
        alerts = self.evaluate(current_metrics, baseline_metrics)
        critical = [a for a in alerts if a.triggered]
        if critical:
            for a in critical:
                logger.info(f"Retraining triggered: {a.reason}")
            return True
        logger.info("Retraining not required. Model indicators are healthy.")
        return False

    def clv_status(self, avg_clv_pct: Optional[float]) -> Dict[str, Any]:
        """Return a structured CLV health status for dashboard/doctor integration."""
        if avg_clv_pct is None:
            return {
                "status": "UNKNOWN",
                "clv_pct": None,
                "threshold_warning": self.clv_warning_threshold,
                "threshold_critical": self.clv_critical_threshold,
            }
        if avg_clv_pct < self.clv_critical_threshold:
            return {
                "status": "CRITICAL",
                "clv_pct": round(avg_clv_pct, 2),
                "action": "RETRAIN_IMMEDIATELY",
            }
        if avg_clv_pct < self.clv_warning_threshold:
            return {
                "status": "WARNING",
                "clv_pct": round(avg_clv_pct, 2),
                "action": "MONITOR_CLOSELY",
            }
        return {
            "status": "HEALTHY",
            "clv_pct": round(avg_clv_pct, 2),
            "action": "NONE",
        }
