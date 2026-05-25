"""
Market-aware decision layer — SharpMoney + DynamicEV + Timing + base DE.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.decision_engine.decision import DecisionIntelligenceEngine
from src.market.sharp_money import SharpMoneyDetector
from src.strategy.timing_engine import StrategyTimingEngine
from src.valuation.dynamic_ev import DynamicEVValuation

logger = logging.getLogger(__name__)


class MarketAwareDecisionEngine:
    def __init__(
        self,
        use_sharp: bool = True,
        use_dynamic_ev: bool = True,
        use_timing: bool = True,
        sharp_min_score: float = 0.3,
        edge_threshold: float = 0.02,
    ):
        self.use_sharp = use_sharp
        self.use_dynamic_ev = use_dynamic_ev
        self.use_timing = use_timing
        self.sharp_min_score = sharp_min_score
        self.edge_threshold = edge_threshold
        self.sharp = SharpMoneyDetector()
        self.dynamic_ev = DynamicEVValuation()
        self.timing = StrategyTimingEngine()
        self.base_de = DecisionIntelligenceEngine(min_ev_threshold=edge_threshold)

    def decide(
        self,
        opportunity: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        market_context = market_context or {}
        edge = float(opportunity.get("edge", 0))
        bet_side = opportunity.get("predicted_outcome", "home")
        if bet_side in ("1", "H"):
            bet_side = "home"
        elif bet_side in ("2", "A"):
            bet_side = "away"

        # 1) Sharp money
        sharp_result = {"sharp_score": 0.5, "safe_to_bet": True}
        if self.use_sharp:
            sharp_result = self.sharp.detect_score(
                opportunity.get("match_id", ""),
                market_context.get("odds_history", []),
                bet_side=bet_side,
            )
            if sharp_result["sharp_score"] < self.sharp_min_score:
                edge *= max(0.25, sharp_result["sharp_score"] / self.sharp_min_score)
                opportunity["edge_adjusted_sharp"] = edge
            if not sharp_result["safe_to_bet"]:
                opportunity["decision"] = "NO_BET"
                opportunity["decision_reason"] = f"Sharp drift against us (score={sharp_result['sharp_score']:.2f})"
                opportunity["market_signals"] = {"sharp": sharp_result}
                return opportunity

        # 2) Dynamic EV timing
        ev_forecast = None
        if self.use_dynamic_ev:
            ev_forecast = self.dynamic_ev.forecast(opportunity, market_context)
            opportunity["ev_current"] = ev_forecast.current_ev
            opportunity["ev_projected"] = ev_forecast.projected_ev
            if ev_forecast.best_action == "NO_BET":
                opportunity["decision"] = "NO_BET"
                opportunity["decision_reason"] = ev_forecast.reason
                opportunity["market_signals"] = {"sharp": sharp_result, "ev": ev_forecast.__dict__}
                return opportunity
            if ev_forecast.best_action == "WAIT":
                opportunity["decision"] = "WAIT"
                opportunity["decision_reason"] = ev_forecast.reason
                opportunity["wait_minutes"] = ev_forecast.wait_minutes
                opportunity["market_signals"] = {"sharp": sharp_result, "ev": ev_forecast.__dict__}
                return opportunity

        # 3) Timing engine (trend vs closing)
        if self.use_timing:
            hours = float(market_context.get("hours_to_kickoff", opportunity.get("hours_to_kickoff", 12)))
            current_odds = float(opportunity.get("bookmaker_odds", 2))
            closing = float(market_context.get("predicted_closing_odds", opportunity.get("pinnacle_odds", current_odds)))
            trend = "DRIFT" if current_odds < closing else "SHORTEN"
            timing = self.timing.evaluate_optimal_entry_time(hours, trend, current_odds, closing)
            if timing["action"] == "WAIT" and hours > 1.0:
                opportunity["decision"] = "WAIT"
                opportunity["decision_reason"] = timing["reason"]
                opportunity["market_signals"] = {"sharp": sharp_result, "timing": timing}
                return opportunity

        # 4) Edge threshold after adjustments
        if edge < self.edge_threshold:
            opportunity["decision"] = "NO_BET"
            opportunity["decision_reason"] = f"Adjusted edge {edge:.2%} below {self.edge_threshold:.2%}"
            return opportunity

        # 5) Base decision engine (liquidity, EV, basic wait)
        stake = opportunity.get("recommended_stake_usd") or opportunity.get("recommended_stake", 10.0)
        base = self.base_de.evaluate_decision(
            event_id=opportunity.get("match_id", "unknown"),
            predicted_probability=opportunity.get("calibrated_prob", 0.5),
            current_odds=opportunity.get("bookmaker_odds", 2.0),
            predicted_closing_odds=float(market_context.get("predicted_closing_odds", opportunity.get("pinnacle_odds", 2.0))),
            hours_to_kickoff=float(market_context.get("hours_to_kickoff", 12)),
            liquidity_available=opportunity.get("liquidity_usd", 5000.0),
            required_stake=stake,
        )
        opportunity["decision"] = base["decision"]
        opportunity["decision_reason"] = base["reason"]
        opportunity["allocated_stake"] = base["allocated_stake"]
        opportunity["market_signals"] = {
            "sharp": sharp_result,
            "ev": ev_forecast.__dict__ if ev_forecast else None,
        }
        return opportunity
