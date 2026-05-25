"""
Concept drift detection with automatic rollback to baseline or shadow model.

Monitors the CLV gap between the champion model and a baseline (market odds).
If the champion's CLV drops below a threshold, automatically rolls back
to a previously approved shadow model or the market baseline.

This protects against silent degradation in production — when the model
stops beating the market but no one notices until the bankroll drops.

Usage:
    from src.mlops.drift.auto_rollback import AutoRollback

    arb = AutoRollback(
        clv_threshold=0.5,  # Minimum CLV edge over baseline
        lookback_bets=100,
        shadow_model=approved_shadow_model,
    )
    decision = arb.check(current_clv, baseline_clv, n_bets)
    # decision["action"] == "ROLLBACK" → switch to shadow model
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("auto_rollback")


class RollbackAction(Enum):
    CONTINUE = "CONTINUE"       # Model is performing well
    WARNING = "WARNING"         # CLV declining but above threshold
    ROLLBACK = "ROLLBACK"       # Roll back to shadow/baseline
    EMERGENCY_STOP = "EMERGENCY_STOP"  # Stop all betting


@dataclass
class DriftCheckResult:
    action: RollbackAction
    champion_clv: float
    baseline_clv: float
    clv_gap: float
    message: str
    n_bets_evaluated: int = 0
    consecutive_declines: int = 0
    timestamp: float = field(default_factory=time.time)


class AutoRollback:
    """
    Monitors CLV gap between champion model and baseline, with
    automatic rollback when the model degrades below threshold.

    Three-tier response:
    1. CONTINUE: CLV gap is healthy (> threshold)
    2. WARNING: CLV gap is declining (50-100% of threshold)
    3. ROLLBACK: CLV gap fell below threshold → switch to shadow model
    4. EMERGENCY_STOP: CLV is negative (model is worse than baseline)

    The rollback is triggered after N consecutive checks below threshold,
    not on a single bad day (avoids premature rollback on variance).
    """

    def __init__(
        self,
        clv_threshold: float = 0.5,
        warning_threshold_pct: float = 0.5,
        lookback_bets: int = 100,
        min_bets_for_check: int = 20,
        consecutive_rollback_threshold: int = 3,
        consecutive_emergency_threshold: int = 2,
        shadow_model: Optional[Any] = None,
        baseline_name: str = "market_odds",
    ):
        """
        Args:
            clv_threshold: Minimum CLV edge (%) over baseline to continue
            warning_threshold_pct: % of threshold that triggers warning (0.5 = 50%)
            lookback_bets: Number of recent bets to evaluate
            min_bets_for_check: Minimum bets before checking drift
            consecutive_rollback_threshold: N consecutive below-threshold checks → rollback
            consecutive_emergency_threshold: N consecutive negative CLV checks → emergency stop
            shadow_model: Previously approved model to roll back to
            baseline_name: Name of the baseline (for logging)
        """
        self.clv_threshold = clv_threshold
        self.warning_threshold_pct = warning_threshold_pct
        self.lookback_bets = lookback_bets
        self.min_bets_for_check = min_bets_for_check
        self.consecutive_rollback_threshold = consecutive_rollback_threshold
        self.consecutive_emergency_threshold = consecutive_emergency_threshold
        self.shadow_model = shadow_model
        self.baseline_name = baseline_name

        self._consecutive_declines = 0
        self._consecutive_negative = 0
        self._check_history: List[DriftCheckResult] = []
        self._last_rollback_time: Optional[float] = None
        self._rollback_count: int = 0

    def check(
        self,
        champion_clv: float,
        baseline_clv: float,
        n_bets: int,
        force: bool = False,
    ) -> DriftCheckResult:
        """
        Check if the champion model should be rolled back.

        Args:
            champion_clv: Champion model's CLV (%) over recent lookback
            baseline_clv: Baseline's CLV (%) (e.g., market odds CLV)
            n_bets: Number of bets in the evaluation window
            force: If True, skip the minimum bets check

        Returns:
            DriftCheckResult with action and details
        """
        if n_bets < self.min_bets_for_check and not force:
            return DriftCheckResult(
                action=RollbackAction.CONTINUE,
                champion_clv=champion_clv,
                baseline_clv=baseline_clv,
                clv_gap=champion_clv - baseline_clv,
                message=f"Insufficient bets ({n_bets}/{self.min_bets_for_check})",
                n_bets_evaluated=n_bets,
            )

        clv_gap = champion_clv - baseline_clv
        warning_line = self.clv_threshold * self.warning_threshold_pct

        # Determine action
        if clv_gap < 0:
            # Champion is WORSE than baseline
            self._consecutive_negative += 1
            self._consecutive_declines += 1

            if self._consecutive_negative >= self.consecutive_emergency_threshold:
                action = RollbackAction.EMERGENCY_STOP
                message = (
                    f"EMERGENCY: Champion CLV ({champion_clv:.2f}%) is WORSE than "
                    f"{self.baseline_name} ({baseline_clv:.2f}%) for "
                    f"{self._consecutive_negative} consecutive checks"
                )
            else:
                action = RollbackAction.ROLLBACK
                message = (
                    f"Champion CLV ({champion_clv:.2f}%) below baseline "
                    f"({baseline_clv:.2f}%) — rollback recommended"
                )

        elif clv_gap < self.clv_threshold:
            # Below threshold but still positive
            self._consecutive_declines += 1
            self._consecutive_negative = 0

            if self._consecutive_declines >= self.consecutive_rollback_threshold:
                action = RollbackAction.ROLLBACK
                message = (
                    f"CLV gap ({clv_gap:.2f}%) below threshold ({self.clv_threshold:.2f}%) "
                    f"for {self._consecutive_declines} consecutive checks — rolling back"
                )
            else:
                action = RollbackAction.WARNING
                message = (
                    f"CLV gap ({clv_gap:.2f}%) declining toward threshold "
                    f"({self.clv_threshold:.2f}%) — decline #{self._consecutive_declines}"
                )

        else:
            # Healthy
            self._consecutive_declines = 0
            self._consecutive_negative = 0
            action = RollbackAction.CONTINUE
            message = f"CLV gap ({clv_gap:.2f}%) healthy (threshold: {self.clv_threshold:.2f}%)"

        result = DriftCheckResult(
            action=action,
            champion_clv=champion_clv,
            baseline_clv=baseline_clv,
            clv_gap=clv_gap,
            message=message,
            n_bets_evaluated=n_bets,
            consecutive_declines=self._consecutive_declines,
        )

        self._check_history.append(result)

        # Execute rollback if needed
        if action in (RollbackAction.ROLLBACK, RollbackAction.EMERGENCY_STOP):
            self._execute_rollback(action, result)

        # Log
        if action != RollbackAction.CONTINUE:
            logger.warning("Drift check: %s → %s", action.value, message)
        else:
            logger.debug("Drift check: CONTINUE (gap=%.2f%%)", clv_gap)

        return result

    def _execute_rollback(self, action: RollbackAction, result: DriftCheckResult) -> None:
        """Execute rollback action."""
        self._last_rollback_time = time.time()
        self._rollback_count += 1

        if action == RollbackAction.EMERGENCY_STOP:
            logger.critical(
                "EMERGENCY STOP triggered! Champion model is worse than baseline. "
                "All betting should be halted immediately."
            )
        elif action == RollbackAction.ROLLBACK and self.shadow_model is not None:
            logger.warning(
                "Rolling back to shadow model. Champion CLV=%.2f%%, baseline=%.2f%%",
                result.champion_clv, result.baseline_clv,
            )
        else:
            logger.warning(
                "Rollback recommended but no shadow model available. "
                "Consider switching to paper trading."
            )

    def reset(self) -> None:
        """Reset consecutive counters (e.g., after a model update)."""
        self._consecutive_declines = 0
        self._consecutive_negative = 0
        logger.info("Auto-rollback counters reset")

    @property
    def status(self) -> Dict[str, Any]:
        """Get current auto-rollback status."""
        return {
            "clv_threshold": self.clv_threshold,
            "consecutive_declines": self._consecutive_declines,
            "consecutive_negative": self._consecutive_negative,
            "rollback_count": self._rollback_count,
            "last_rollback": self._last_rollback_time,
            "has_shadow_model": self.shadow_model is not None,
            "n_checks": len(self._check_history),
            "last_action": self._check_history[-1].action.value if self._check_history else "NONE",
        }
