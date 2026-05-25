"""Dynamic EV and timing forecast for BET vs WAIT decisions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np


@dataclass
class EVTimingForecast:
    best_action: str  # BET_NOW | WAIT | NO_BET
    current_ev: float
    projected_ev: float
    wait_minutes: int
    reason: str


class DynamicEVValuation:
    def __init__(self, wait_ev_gain_threshold: float = 0.005):
        self.wait_ev_gain_threshold = wait_ev_gain_threshold

    def calculate_dynamic_ev(self, model_prob: float, current_odds: float) -> float:
        if current_odds <= 1.0:
            return -1.0
        return float((model_prob * current_odds) - 1.0)

    def estimate_ev_decay_rate(
        self,
        current_ev: float,
        hours_to_kickoff: float,
        market_efficiency_score: float = 0.90,
    ) -> float:
        if hours_to_kickoff <= 0:
            return 0.0
        alpha = market_efficiency_score / max(1.0, hours_to_kickoff)
        decayed_ev = current_ev * np.exp(-alpha * 0.5)
        return float(current_ev - decayed_ev)

    def forecast(
        self,
        opportunity: Dict[str, Any],
        market_context: Dict[str, Any],
    ) -> EVTimingForecast:
        """
        Forecast whether to bet now or wait based on EV trajectory and closing line expectation.
        """
        prob = float(opportunity.get("calibrated_prob", 0.5))
        current_odds = float(opportunity.get("bookmaker_odds", 2.0))
        closing_odds = float(
            market_context.get("predicted_closing_odds")
            or opportunity.get("pinnacle_odds")
            or current_odds
        )
        hours = float(market_context.get("hours_to_kickoff", opportunity.get("hours_to_kickoff", 12.0)))
        minutes_to_kickoff = max(0.0, hours * 60.0)

        current_ev = self.calculate_dynamic_ev(prob, current_odds)
        projected_ev_at_close = self.calculate_dynamic_ev(prob, closing_odds)

        if current_ev < 0.01:
            return EVTimingForecast("NO_BET", current_ev, projected_ev_at_close, 0, "EV below minimum")

        # Odds expected to rise (better price for backer) → WAIT if time allows
        if current_odds < closing_odds * 0.99 and minutes_to_kickoff > 120:
            gain = projected_ev_at_close - current_ev
            if gain >= self.wait_ev_gain_threshold:
                wait_mins = min(int(minutes_to_kickoff * 0.25), 180)
                return EVTimingForecast(
                    "WAIT",
                    current_ev,
                    projected_ev_at_close,
                    wait_mins,
                    f"EV may improve +{gain:.2%} if line drifts to {closing_odds:.2f}",
                )

        # Odds shortening (steam) → bet now before edge erodes
        if current_odds > closing_odds * 1.02:
            return EVTimingForecast(
                "BET_NOW",
                current_ev,
                projected_ev_at_close,
                0,
                "Line expected to shorten; capture edge now",
            )

        decay = self.estimate_ev_decay_rate(current_ev, hours)
        if decay > current_ev * 0.3 and minutes_to_kickoff > 60:
            return EVTimingForecast(
                "WAIT",
                current_ev,
                current_ev - decay,
                30,
                "EV decay risk high near kickoff; wait for clarity",
            )

        return EVTimingForecast(
            "BET_NOW",
            current_ev,
            projected_ev_at_close,
            0,
            "Stable EV window",
        )
