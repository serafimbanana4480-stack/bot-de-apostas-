import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class ValueBetFilter:
    """
    Hedge-fund grade Multi-Factor Value Bet Filter.
    Applies strict pre-trade checks to ensure only high-confidence,
    highly liquid, and mathematically optimized opportunities are selected.
    """
    def __init__(
        self,
        min_edge: float = 0.05,            # Minimum model edge (5%)
        min_odd: float = 1.50,             # Minimum decimal odds
        min_probability: float = 0.60,      # Minimum calibrated probability (60%)
        max_time_to_event_hours: float = 48.0, # Freshness window
        max_adverse_line_drop_2h: float = 0.03, # 3% maximum adverse drop in odds (sharp money against us)
        max_odds: float = 5.0,
        edge_threshold_by_bin: Optional[Dict[Tuple[float, float], float]] = None,
        min_liquidity_proxy: Optional[float] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.min_edge = min_edge
        self.min_odd = min_odd
        self.min_probability = min_probability
        self.max_time_to_event_hours = max_time_to_event_hours
        self.max_adverse_line_drop_2h = max_adverse_line_drop_2h
        self.max_odds = max_odds
        self.edge_threshold_by_bin = edge_threshold_by_bin or {
            (1.0, 2.0): 0.02,
            (2.0, 3.0): 0.03,
            (3.0, 5.0): 0.05,
            (5.0, float("inf")): 0.10,
        }
        self.min_liquidity_proxy = min_liquidity_proxy

    @staticmethod
    def _odds_bin(odds: float) -> Tuple[float, float]:
        if odds < 2.0:
            return (1.0, 2.0)
        if odds < 3.0:
            return (2.0, 3.0)
        if odds < 5.0:
            return (3.0, 5.0)
        return (5.0, float("inf"))

    def evaluate(self, opportunity: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates a single bet opportunity against all professional risk filters.
        
        Opportunity Dictionary Format:
        {
            "match_id": str,
            "event_name": str,
            "calibrated_prob": float,
            "bookmaker_odds": float,
            "pinnacle_odds": Optional[float],
            "event_time": datetime,
            "has_critical_injury_24h": bool,
            "odds_2h_ago": Optional[float],
            "liquidity_usd": float,
            "min_liquidity_required": float,
            "historical_roi_positive": bool
        }
        
        Returns:
            Tuple[bool, Optional[str]]: (passed_filters, reason_for_failure)
        """
        match_id = opportunity.get("match_id", "unknown")
        event_name = opportunity.get("event_name", "unknown")
        prob = opportunity.get("calibrated_prob", 0.0)
        odds = opportunity.get("bookmaker_odds", 1.0)
        pinnacle_odds = opportunity.get("pinnacle_odds")
        event_time = opportunity.get("event_time")
        has_injury = opportunity.get("has_critical_injury_24h", False)
        odds_2h_ago = opportunity.get("odds_2h_ago")
        liquidity = opportunity.get("liquidity_usd", 0.0)
        min_liq_req = opportunity.get("min_liquidity_required", 1000.0)
        hist_roi = opportunity.get("historical_roi_positive", True)
        liquidity_proxy = opportunity.get("liquidity_proxy", opportunity.get("betfair_volume"))

        # 0. Hard cap on extreme longshots / low-liquidity outliers.
        if odds > self.max_odds:
            reason = f"Odds {odds:.2f} above hard cap {self.max_odds:.2f}"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # Bin-aware minimum edge thresholds.
        bin_key = self._odds_bin(odds)
        min_edge_for_bin = self.edge_threshold_by_bin.get(bin_key, self.min_edge)

        # 1. Minimum Calibrated Probability Filter
        if prob < self.min_probability:
            reason = f"Calibrated probability {prob:.2%} below threshold of {self.min_probability:.2%}"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # 2. Minimum Odds Filter
        if odds < self.min_odd:
            reason = f"Odds {odds:.2f} below threshold of {self.min_odd:.2f}"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # 3. Mathematical Edge Filter: edge = prob - (1 / odds)
        implied_prob = 1.0 / odds if odds > 0 else 1.0
        edge = prob - implied_prob
        if edge < min_edge_for_bin:
            reason = f"Estimated edge {edge:.2%} below threshold of {min_edge_for_bin:.2%}"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # 4. Pinnacle Odds Reference Check (Market Efficiency Baseline)
        if pinnacle_odds is None or pinnacle_odds <= 1.0:
            reason = "No valid Pinnacle reference odds available (required for efficiency check)"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # 5. Injury Check
        if has_injury:
            reason = "Critical injury flagged in last 24h that might not be fully priced"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # 6. Sharp Money Line Movement Check
        # If the odds are dropping rapidly, sharp money is moving in the opposite direction.
        if odds_2h_ago is not None and odds_2h_ago > 1.0:
            line_drop = (odds_2h_ago - odds) / odds_2h_ago
            if line_drop > self.max_adverse_line_drop_2h:
                reason = f"Adverse line movement detected: odds dropped by {line_drop:.2%} in 2h (limit {self.max_adverse_line_drop_2h:.2%})"
                self.logger.info(f"[{event_name}] Rejected: {reason}")
                return False, reason

        # 7. Liquidity Verification
        if liquidity < min_liq_req:
            reason = f"Insufficient market liquidity: ${liquidity:,.2f} available, required ${min_liq_req:,.2f}"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        # Optional liquidity proxy: when we have exchange/bookmaker volume, use it
        # to avoid thin longshots even if a stake-sized liquidity estimate exists.
        if self.min_liquidity_proxy is not None and liquidity_proxy is not None and odds >= 3.0:
            if float(liquidity_proxy) < self.min_liquidity_proxy:
                reason = (
                    f"Liquidity proxy {float(liquidity_proxy):,.2f} below minimum "
                    f"{self.min_liquidity_proxy:,.2f} for longshot bin"
                )
                self.logger.info(f"[{event_name}] Rejected: {reason}")
                return False, reason

        # Historical CLV check per bin when upstream analytics provides it.
        hist_clv_by_bin = opportunity.get("historical_clv_pct_by_bin")
        if isinstance(hist_clv_by_bin, dict) and odds >= 3.0:
            hist_clv = hist_clv_by_bin.get(bin_key)
            if hist_clv is not None and float(hist_clv) < 0:
                reason = f"Historical CLV for bin {bin_key} is negative ({float(hist_clv):.2f}%)"
                self.logger.info(f"[{event_name}] Rejected: {reason}")
                return False, reason

        # 8. Event Freshness (Data relevance window: 24-48h)
        if event_time:
            now = datetime.now()
            hours_until_event = (event_time - now).total_seconds() / 3600.0
            if hours_until_event < 0:
                reason = "Event already started or finished"
                self.logger.info(f"[{event_name}] Rejected: {reason}")
                return False, reason
            if hours_until_event > self.max_time_to_event_hours:
                reason = f"Event is too far in the future ({hours_until_event:.1f}h until start, max {self.max_time_to_event_hours}h)"
                self.logger.info(f"[{event_name}] Rejected: {reason}")
                return False, reason

        # 9. Historical Backtest Verification Check
        if not hist_roi:
            reason = "Historical backtest for this specific sport/league/edge subsegment has negative ROI"
            self.logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason

        self.logger.info(f"[{event_name}] Passed all pre-trade filters. Edge: {edge:.2%}, Odds: {odds:.2f}")
        return True, None
