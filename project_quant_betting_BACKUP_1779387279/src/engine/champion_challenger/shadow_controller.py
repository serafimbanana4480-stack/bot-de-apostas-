"""
Shadow Controller — Parallel Model Evaluation.

Runs champion and challenger models side-by-side on live opportunities
*without* placing real wagers for the challenger.  Tracks structured
performance metrics and supports auto-promotion when the challenger
demonstrably outperforms.

Reference (improved from):
    Projeto de Apostas › src/mlops/shadow_controller.py
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocols / Contracts
# ---------------------------------------------------------------------------

class PredictionFunc(Protocol):
    """Any callable that returns a probability [0-1]."""
    def __call__(self) -> float: ...


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class VirtualDecision(str, Enum):
    BET = "BET"
    SKIP = "SKIP"


class ShadowLogEntry(BaseModel):
    """One shadow evaluation record."""
    event_id: str
    current_odds: float
    champion_id: str
    challenger_id: str
    champion_prob: float
    challenger_prob: float
    champion_ev: float
    challenger_ev: float
    champion_decision: VirtualDecision
    challenger_decision: VirtualDecision
    agreement: bool = Field(description="True when both models agree on the decision.")
    actual_outcome: Optional[bool] = Field(
        default=None, description="Filled after settlement: True = outcome happened."
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelPerformance(BaseModel):
    """Aggregate performance metrics for one model in shadow mode."""
    model_id: str
    total_decisions: int = 0
    bets_taken: int = 0
    correct_bets: int = 0
    incorrect_bets: int = 0
    skips: int = 0
    accuracy: float = 0.0
    avg_ev: float = 0.0
    calibration_error: float = 0.0  # mean |predicted_prob - actual_rate|


class ShadowPerformanceReport(BaseModel):
    """Full shadow performance comparison."""
    champion: ModelPerformance
    challenger: ModelPerformance
    total_events: int
    agreement_rate: float = Field(description="Fraction where both models agree.")
    discrepancy_count: int
    should_promote_challenger: bool
    promotion_reason: str


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ShadowConfig:
    """Tunable parameters for shadow controller."""
    ev_threshold: float = 0.02           # 2 % minimum EV to trigger virtual BET
    min_events_for_promotion: int = 100
    promotion_accuracy_delta: float = 0.03    # challenger must beat champion by ≥ 3 pp
    promotion_ev_delta: float = 0.005         # challenger avg EV must exceed champion by ≥ 0.5 pp


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ShadowController:
    """Runs champion and challenger models in parallel shadow mode.

    Improvements over reference:
    * Structured ``ShadowLogEntry`` with Pydantic validation.
    * Post-settlement accuracy tracking.
    * Auto-promotion rules with configurable deltas.
    * Calibration error metric.

    Args:
        champion_id: Identifier for the champion model.
        challenger_id: Identifier for the challenger model.
        config: Shadow evaluation parameters.
    """

    def __init__(
        self,
        champion_id: str,
        challenger_id: str,
        config: ShadowConfig | None = None,
    ) -> None:
        self.champion_id = champion_id
        self.challenger_id = challenger_id
        self.config = config or ShadowConfig()
        self._logs: list[ShadowLogEntry] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_opportunity(
        self,
        event_id: str,
        current_odds: float,
        champion_predict: Callable[[], float],
        challenger_predict: Callable[[], float],
    ) -> ShadowLogEntry:
        """Evaluate a single opportunity with both models.

        Args:
            event_id: Unique event identifier.
            current_odds: Current decimal odds.
            champion_predict: Callable returning champion's probability.
            challenger_predict: Callable returning challenger's probability.

        Returns:
            ``ShadowLogEntry`` with both predictions and virtual decisions.
        """
        p_champ = champion_predict()
        p_chall = challenger_predict()

        ev_champ = p_champ * current_odds - 1.0
        ev_chall = p_chall * current_odds - 1.0

        threshold = self.config.ev_threshold
        dec_champ = VirtualDecision.BET if ev_champ > threshold else VirtualDecision.SKIP
        dec_chall = VirtualDecision.BET if ev_chall > threshold else VirtualDecision.SKIP

        entry = ShadowLogEntry(
            event_id=event_id,
            current_odds=current_odds,
            champion_id=self.champion_id,
            challenger_id=self.challenger_id,
            champion_prob=p_champ,
            challenger_prob=p_chall,
            champion_ev=ev_champ,
            challenger_ev=ev_chall,
            champion_decision=dec_champ,
            challenger_decision=dec_chall,
            agreement=(dec_champ == dec_chall),
        )

        self._logs.append(entry)
        logger.info(
            "Shadow [%s]: champ=%s (EV=%.4f)  chall=%s (EV=%.4f)  agree=%s",
            event_id, dec_champ.value, ev_champ, dec_chall.value, ev_chall, entry.agreement,
        )
        return entry

    def settle_outcome(self, event_id: str, outcome: bool) -> int:
        """Record the actual outcome for a previously evaluated event.

        Args:
            event_id: The event that has settled.
            outcome: True if the predicted outcome occurred.

        Returns:
            Number of log entries updated.
        """
        updated = 0
        for entry in self._logs:
            if entry.event_id == event_id and entry.actual_outcome is None:
                entry.actual_outcome = outcome
                updated += 1
        return updated

    def get_performance_report(self) -> ShadowPerformanceReport:
        """Generate aggregate performance comparison.

        Returns:
            ``ShadowPerformanceReport`` with metrics and promotion recommendation.
        """
        champ_perf = self._compute_performance(self.champion_id, is_champion=True)
        chall_perf = self._compute_performance(self.challenger_id, is_champion=False)

        total = len(self._logs)
        agreements = sum(1 for e in self._logs if e.agreement)
        agreement_rate = agreements / max(total, 1)
        discrepancies = total - agreements

        should_promote, reason = self._evaluate_promotion(champ_perf, chall_perf)

        return ShadowPerformanceReport(
            champion=champ_perf,
            challenger=chall_perf,
            total_events=total,
            agreement_rate=agreement_rate,
            discrepancy_count=discrepancies,
            should_promote_challenger=should_promote,
            promotion_reason=reason,
        )

    @property
    def logs(self) -> list[ShadowLogEntry]:
        """Access raw shadow logs (read-only copy)."""
        return list(self._logs)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _compute_performance(self, model_id: str, is_champion: bool) -> ModelPerformance:
        """Compute aggregate metrics for one model from settled entries."""
        settled = [e for e in self._logs if e.actual_outcome is not None]

        bets_taken = 0
        correct = 0
        incorrect = 0
        skips = 0
        ev_values: list[float] = []
        calibration_errors: list[float] = []

        for entry in settled:
            if is_champion:
                decision = entry.champion_decision
                prob = entry.champion_prob
                ev = entry.champion_ev
            else:
                decision = entry.challenger_decision
                prob = entry.challenger_prob
                ev = entry.challenger_ev

            if decision == VirtualDecision.BET:
                bets_taken += 1
                ev_values.append(ev)
                if entry.actual_outcome:
                    correct += 1
                else:
                    incorrect += 1
            else:
                skips += 1

            # Calibration: |predicted_prob - actual_rate|
            actual_val = 1.0 if entry.actual_outcome else 0.0
            calibration_errors.append(abs(prob - actual_val))

        accuracy = correct / max(bets_taken, 1)
        avg_ev = statistics.mean(ev_values) if ev_values else 0.0
        calibration = statistics.mean(calibration_errors) if calibration_errors else 0.0

        return ModelPerformance(
            model_id=model_id,
            total_decisions=len(settled),
            bets_taken=bets_taken,
            correct_bets=correct,
            incorrect_bets=incorrect,
            skips=skips,
            accuracy=accuracy,
            avg_ev=avg_ev,
            calibration_error=calibration,
        )

    def _evaluate_promotion(
        self, champ: ModelPerformance, chall: ModelPerformance,
    ) -> tuple[bool, str]:
        """Decide whether to promote the challenger."""
        cfg = self.config

        if chall.total_decisions < cfg.min_events_for_promotion:
            return False, (
                f"Insufficient settled events ({chall.total_decisions} < {cfg.min_events_for_promotion})."
            )

        acc_delta = chall.accuracy - champ.accuracy
        ev_delta = chall.avg_ev - champ.avg_ev

        if acc_delta >= cfg.promotion_accuracy_delta and ev_delta >= cfg.promotion_ev_delta:
            return True, (
                f"Challenger outperforms: accuracy +{acc_delta:.4f} (≥{cfg.promotion_accuracy_delta}), "
                f"EV +{ev_delta:.4f} (≥{cfg.promotion_ev_delta})."
            )

        return False, (
            f"Challenger does not sufficiently outperform: "
            f"accuracy delta={acc_delta:+.4f}, EV delta={ev_delta:+.4f}."
        )
