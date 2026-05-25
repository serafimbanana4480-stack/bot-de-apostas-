from typing import Any, Dict


class DecisionIntelligenceEngine:
    """
    Decides the final action (BET, WAIT, or NO_BET) by cross-referencing
    model predictions, odds dynamics, timing curves, and bookmaker profiles.
    """
    def __init__(self, min_ev_threshold: float = 0.02):
        self.min_ev_threshold = min_ev_threshold

    def evaluate_decision(
        self,
        event_id: str,
        predicted_probability: float,
        current_odds: float,
        predicted_closing_odds: float,
        hours_to_kickoff: float,
        liquidity_available: float,
        required_stake: float,
        edge_decay_per_hour: float = 0.005,
    ) -> Dict[str, Any]:
        """
        State machine to compute the optimal execution state.
        
        Instead of a fixed TTL (e.g. 5 minutes), the signal remains valid
        until the odds drop below the minimum acceptable odds calculated from
        the EV threshold plus edge decay over time.
        """
        # 1. Base EV Check
        ev = (predicted_probability * current_odds) - 1.0
        if ev < self.min_ev_threshold:
            return {
                "decision": "NO_BET",
                "reason": f"EV {ev:.3f} below threshold {self.min_ev_threshold}",
                "allocated_stake": 0.0,
                "min_acceptable_odds": None,
            }

        # 2. Liquidity validation
        if liquidity_available < required_stake:
            return {
                "decision": "NO_BET",
                "reason": f"Insufficient market liquidity ({liquidity_available} vs required {required_stake})",
                "allocated_stake": 0.0,
                "min_acceptable_odds": None,
            }

        # 3. Compute minimum acceptable odds with edge decay
        # As time passes, edge decays (information gets priced in)
        decayed_edge = max(0.0, self.min_ev_threshold - edge_decay_per_hour * max(0, hours_to_kickoff))
        min_acceptable_odds = (1.0 + decayed_edge) / predicted_probability if predicted_probability > 0 else float('inf')

        # 4. Timing drift check
        if current_odds < predicted_closing_odds:
            if hours_to_kickoff > 2.0:
                return {
                    "decision": "WAIT",
                    "reason": f"Expect odds to rise to predicted close {predicted_closing_odds:.2f} (current: {current_odds:.2f})",
                    "allocated_stake": 0.0,
                    "min_acceptable_odds": min_acceptable_odds,
                }

        return {
            "decision": "BET_NOW",
            "reason": f"Optimal entry: EV {ev:.3f} >= threshold, sufficient liquidity, efficient execution window",
            "allocated_stake": required_stake,
            "min_acceptable_odds": min_acceptable_odds,
        }
