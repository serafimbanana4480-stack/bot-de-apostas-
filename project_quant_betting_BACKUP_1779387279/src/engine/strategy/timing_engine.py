"""
Strategy Timing Engine.

Determines optimal bet entry timing via EV curve analysis, confidence
thresholds, and time-to-kickoff urgency modelling.  Outputs a three-state
decision — BET_NOW / WAIT / NO_BET — with a full audit trail.

Reference (improved from):
    Projeto de Apostas › src/strategy/timing_engine.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class TimingAction(str, Enum):
    """Three-state timing decision."""
    BET_NOW = "BET_NOW"
    WAIT = "WAIT"
    NO_BET = "NO_BET"


class OddsTrend(str, Enum):
    """Market trend prediction."""
    SHORTEN = "SHORTEN"     # odds going down (value disappearing)
    DRIFT = "DRIFT"         # odds going up (value increasing)
    STABLE = "STABLE"       # no significant movement


class TimingDecision(BaseModel):
    """Immutable timing evaluation result with full audit trail."""
    action: TimingAction
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the decision [0-1].")
    reason: str
    urgency_score: float = Field(ge=0.0, le=1.0, description="Time-pressure urgency [0-1].")
    expected_ev_now: float = Field(description="EV if we bet now (% of stake).")
    expected_ev_wait: float = Field(description="Estimated EV if we wait (% of stake).")
    expected_ev_delta: float = Field(description="EV_now - EV_wait. Positive ⇒ bet now.")
    expected_slippage: float = Field(default=0.0, description="Expected value lost if we wait.")
    hours_to_kickoff: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class TimingConfig:
    """Tunable knobs for the timing engine."""
    # EV thresholds
    min_ev_threshold: float = 0.02           # 2% EV floor to consider a bet
    ev_wait_premium: float = 0.015           # extra EV needed to justify WAIT

    # Confidence
    min_confidence_to_bet: float = 0.55      # minimum model confidence to bet

    # Urgency (exponential decay)
    urgency_half_life_hours: float = 6.0     # hours at which urgency = 0.5
    urgency_cutoff_hours: float = 0.25       # below this → urgency = 1.0 (force bet)

    # Timing windows
    max_hours_to_wait: float = 48.0          # don't wait longer than this
    min_hours_for_wait: float = 1.0          # if <1 h to kick-off, never WAIT

    # Slippage model
    slippage_per_hour_pct: float = 0.003     # 0.3% assumed slippage per hour waited


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TimingEngine:
    """Evaluates optimal bet placement timing.

    Improvements over reference:
    * Three-state output (adds NO_BET).
    * Exponential urgency model instead of hard 1-hour cut-off.
    * EV-curve comparison between *bet now* and *wait*.
    * Explicit confidence gating.
    * Immutable Pydantic result with audit fields.

    Args:
        config: Timing parameters.  Defaults are sensible for pre-match soccer.
    """

    def __init__(self, config: Optional[TimingConfig] = None) -> None:
        self.config = config or TimingConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        hours_to_kickoff: float,
        predicted_trend: OddsTrend | str,
        current_odds: float,
        predicted_closing_odds: float,
        model_probability: float,
        model_confidence: float = 0.70,
    ) -> TimingDecision:
        """Evaluate optimal entry timing for a single opportunity.

        Args:
            hours_to_kickoff: Time remaining until the event starts.
            predicted_trend: Expected odds movement direction.
            current_odds: Current decimal odds.
            predicted_closing_odds: Model-predicted closing odds.
            model_probability: Model-estimated win probability [0-1].
            model_confidence: Confidence in the model's probability [0-1].

        Returns:
            ``TimingDecision`` with action, reasoning, and audit trail.
        """
        trend = OddsTrend(predicted_trend) if isinstance(predicted_trend, str) else predicted_trend
        cfg = self.config

        # --- 1. Compute EV curves ----------------------------------------
        ev_now = self._compute_ev(model_probability, current_odds)
        ev_wait = self._estimate_ev_wait(
            model_probability, current_odds, predicted_closing_odds, trend, hours_to_kickoff,
        )
        ev_delta = ev_now - ev_wait

        # --- 2. Urgency ---------------------------------------------------
        urgency = self._compute_urgency(hours_to_kickoff)

        # --- 3. Confidence gating -----------------------------------------
        if model_confidence < cfg.min_confidence_to_bet:
            return TimingDecision(
                action=TimingAction.NO_BET,
                confidence=model_confidence,
                reason=f"Model confidence {model_confidence:.2%} below threshold {cfg.min_confidence_to_bet:.2%}.",
                urgency_score=urgency,
                expected_ev_now=ev_now,
                expected_ev_wait=ev_wait,
                expected_ev_delta=ev_delta,
                hours_to_kickoff=hours_to_kickoff,
            )

        # --- 4. EV floor ---------------------------------------------------
        if ev_now < cfg.min_ev_threshold and ev_wait < cfg.min_ev_threshold:
            return TimingDecision(
                action=TimingAction.NO_BET,
                confidence=model_confidence,
                reason=f"EV_now ({ev_now:.4f}) and EV_wait ({ev_wait:.4f}) below threshold {cfg.min_ev_threshold:.4f}.",
                urgency_score=urgency,
                expected_ev_now=ev_now,
                expected_ev_wait=ev_wait,
                expected_ev_delta=ev_delta,
                hours_to_kickoff=hours_to_kickoff,
            )

        # --- 5. Decision logic --------------------------------------------
        action, reason = self._decide(
            ev_now, ev_wait, ev_delta, trend, urgency, hours_to_kickoff,
        )

        slippage = self._estimate_slippage(hours_to_kickoff) if action == TimingAction.WAIT else 0.0

        return TimingDecision(
            action=action,
            confidence=model_confidence,
            reason=reason,
            urgency_score=urgency,
            expected_ev_now=ev_now,
            expected_ev_wait=ev_wait,
            expected_ev_delta=ev_delta,
            expected_slippage=slippage,
            hours_to_kickoff=hours_to_kickoff,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ev(probability: float, odds: float) -> float:
        """EV = p * odds - 1."""
        return probability * odds - 1.0

    def _estimate_ev_wait(
        self,
        probability: float,
        current_odds: float,
        predicted_closing_odds: float,
        trend: OddsTrend,
        hours_to_kickoff: float,
    ) -> float:
        """Estimate EV if we wait for closing odds minus slippage."""
        raw_ev_wait = self._compute_ev(probability, predicted_closing_odds)
        slippage = self._estimate_slippage(hours_to_kickoff)
        return raw_ev_wait - slippage

    def _estimate_slippage(self, hours_to_kickoff: float) -> float:
        """Slippage grows linearly with time we wait (simplified)."""
        wait_hours = min(hours_to_kickoff, self.config.max_hours_to_wait)
        return wait_hours * self.config.slippage_per_hour_pct

    def _compute_urgency(self, hours_to_kickoff: float) -> float:
        """Exponential decay urgency: 1.0 at kick-off → 0 far out.

        Formula: urgency = exp(-ln(2) / half_life * hours)
        Clamped to 1.0 below cutoff.
        """
        cfg = self.config
        if hours_to_kickoff <= cfg.urgency_cutoff_hours:
            return 1.0

        decay_rate = math.log(2) / cfg.urgency_half_life_hours
        return math.exp(-decay_rate * hours_to_kickoff)

    def _decide(
        self,
        ev_now: float,
        ev_wait: float,
        ev_delta: float,
        trend: OddsTrend,
        urgency: float,
        hours_to_kickoff: float,
    ) -> tuple[TimingAction, str]:
        """Core decision heuristic."""
        cfg = self.config

        # Urgency override — very close to kick-off
        if hours_to_kickoff < cfg.min_hours_for_wait:
            return (
                TimingAction.BET_NOW,
                f"Kick-off imminent ({hours_to_kickoff:.1f} h). Executing now to guarantee fill.",
            )

        # Shortening odds — value disappearing
        if trend == OddsTrend.SHORTEN:
            return (
                TimingAction.BET_NOW,
                f"Odds shortening (trend={trend.value}). Locking current value. EV_delta={ev_delta:+.4f}.",
            )

        # Drifting odds — value increasing, but only wait if EV premium justifies it
        if trend == OddsTrend.DRIFT:
            if ev_wait > ev_now + cfg.ev_wait_premium:
                return (
                    TimingAction.WAIT,
                    f"Odds drifting. EV_wait ({ev_wait:.4f}) exceeds EV_now ({ev_now:.4f}) "
                    f"by {ev_wait - ev_now:.4f} > premium {cfg.ev_wait_premium:.4f}.",
                )
            # Drift but premium not worth the risk
            return (
                TimingAction.BET_NOW,
                f"Odds drifting but wait premium ({ev_wait - ev_now:.4f}) insufficient vs. threshold {cfg.ev_wait_premium:.4f}.",
            )

        # Stable market — use urgency as tiebreaker
        if urgency > 0.5:
            return (
                TimingAction.BET_NOW,
                f"Stable market with high urgency ({urgency:.2f}). Betting now.",
            )

        return (
            TimingAction.BET_NOW,
            f"Stable market, positive EV. Default: bet now.",
        )
