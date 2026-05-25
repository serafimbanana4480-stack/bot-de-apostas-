import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.risk.kelly import calculate_fractional_kelly
from src.risk.value_filter import ValueBetFilter


class PortfolioOptimizer:
    """
    Hedge-fund grade Capital Allocation and Risk Control Engine.
    1. Filters opportunities via multi-factor pre-trade rules.
    2. Dynamically scales Kelly staking based on current system drawdowns.
    3. Caps single bets at strict limits (2-5% of bankroll).
    4. Limits total daily exposure to 15-20%, automatically scaling down wagers pro-rata.
    5. Evaluates circuit breakers to halt wagering under catastrophic drawdowns.
    """
    def __init__(
        self,
        initial_bankroll: float = 10000.0,
        max_daily_exposure_pct: float = 0.15,  # Max total wagers today (15% bankroll)
        max_stake_per_bet_pct: float = 0.02,   # Max stake on single bet (2% bankroll)
        kelly_multiplier: float = 0.25,        # Fractional Kelly (Quarter-Kelly)
        max_drawdown_limit_pct: float = 0.20,  # Halt system if peak-to-trough drawdown > 20%
        min_edge: float = 0.05                 # 5% minimum model edge
    ):
        self.logger = logging.getLogger(__name__)
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        
        self.max_daily_exposure_pct = max_daily_exposure_pct
        self.max_stake_per_bet_pct = max_stake_per_bet_pct
        self.kelly_multiplier = kelly_multiplier
        self.max_drawdown_limit_pct = max_drawdown_limit_pct
        self.min_edge = min_edge
        
        self.value_filter = ValueBetFilter(min_edge=min_edge)

    def update_bankroll(self, current_val: float):
        """Updates current bankroll and records high-water peak for drawdown checks."""
        self.current_bankroll = current_val
        if current_val > self.peak_bankroll:
            self.peak_bankroll = current_val
            
    def get_current_drawdown(self) -> float:
        """Calculates current peak-to-trough drawdown."""
        if self.peak_bankroll <= 0:
            return 0.0
        return (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll

    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Verifies if system-wide circuit breakers are triggered.
        Returns:
            Tuple[bool, str]: (is_active_halt, reason_message)
        """
        drawdown = self.get_current_drawdown()
        if drawdown >= self.max_drawdown_limit_pct:
            msg = f"System Halted: Peak-to-Trough drawdown {drawdown:.2%} breached maximum safety limit of {self.max_drawdown_limit_pct:.2%}"
            self.logger.critical(msg)
            return True, msg
        return False, "System status normal. Circuit breakers nominal."

    def optimize_daily_portfolio(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of raw opportunities, validates them through the Multi-Factor Filter,
        and sizes the wagers with Kelly allocation, daily exposure scaling, and single bet caps.
        
        Input list of dicts must contain:
        {
            "match_id": str,
            "event_name": str,
            "calibrated_prob": float,
            "bookmaker_odds": float,
            "pinnacle_odds": float,
            "event_time": datetime,
            ...other ValueBetFilter required fields...
        }
        
        Returns:
            List[Dict[str, Any]]: Approved opportunities with calculated sizing and recommended stakes.
        """
        self.logger.info("Starting daily portfolio optimization process...")
        
        # 1. Check Circuit Breaker
        halted, reason = self.check_circuit_breaker()
        if halted:
            self.logger.warning(f"All wagering blocked: {reason}")
            return []

        # 2. Filter opportunities
        filtered_opportunities = []
        for opp in opportunities:
            passed, reject_reason = self.value_filter.evaluate(opp)
            if passed:
                filtered_opportunities.append(opp)
            else:
                opp["status"] = "rejected"
                opp["reject_reason"] = reject_reason

        if not filtered_opportunities:
            self.logger.info("No opportunities passed the multi-factor value filters today.")
            return []

        # 3. Calculate Sizing for each passed opportunity using dynamic drawdown-conditioned Kelly
        drawdown = self.get_current_drawdown()
        # Scale factor downscales sizing linearly as we approach the max drawdown safety limit
        drawdown_scale = 1.0 - (drawdown / self.max_drawdown_limit_pct) if drawdown < self.max_drawdown_limit_pct else 0.0
        drawdown_scale = max(0.0, drawdown_scale)

        approved_bets = []
        total_recommended_fraction = 0.0

        for opp in filtered_opportunities:
            prob = opp["calibrated_prob"]
            odds = opp["bookmaker_odds"]
            
            # Base Fractional Kelly Fraction (of bankroll)
            raw_kelly = calculate_fractional_kelly(prob, odds, kelly_multiplier=self.kelly_multiplier)
            
            # Apply drawdown scaling
            scaled_kelly = raw_kelly * drawdown_scale
            
            # Cap single bet allocation (ex: max 2% of bankroll)
            final_kelly_fraction = min(scaled_kelly, self.max_stake_per_bet_pct)
            
            if final_kelly_fraction > 0.0:
                opp["raw_kelly_fraction"] = raw_kelly
                opp["final_kelly_fraction"] = final_kelly_fraction
                total_recommended_fraction += final_kelly_fraction
                approved_bets.append(opp)

        if not approved_bets:
            self.logger.info("All opportunities were sized down to zero due to drawdown or caps.")
            return []

        # 4. Enforce Maximum Daily Exposure (Pro-Rata Downscaling)
        # If the sum of all individual stakes exceeds our total daily risk cap (ex: 15% bankroll),
        # we scale down all approved stakes proportionally to fit the daily cap exactly.
        if total_recommended_fraction > self.max_daily_exposure_pct:
            scale_ratio = self.max_daily_exposure_pct / total_recommended_fraction
            self.logger.warning(
                f"Total daily recommendation ({total_recommended_fraction:.2%}) exceeds cap ({self.max_daily_exposure_pct:.2%}). "
                f"Applying pro-rata downscaling ratio: {scale_ratio:.4f}"
            )
            for bet in approved_bets:
                bet["final_kelly_fraction"] *= scale_ratio
        
        # 5. Convert Fractions to USD Stakes & finalize bet list
        final_bets = []
        for bet in approved_bets:
            fraction = bet["final_kelly_fraction"]
            stake_usd = self.current_bankroll * fraction
            
            # Skip micro stakes (e.g. less than 0.1% bankroll)
            if fraction < 0.001:
                self.logger.info(f"Skipping bet on [{bet['event_name']}] - Sized below minimum trade threshold.")
                continue
                
            bet["recommended_stake_usd"] = round(stake_usd, 2)
            bet["edge"] = bet["calibrated_prob"] - (1.0 / bet["bookmaker_odds"])
            bet["status"] = "approved"
            
            self.logger.info(
                f"Approved Value Bet: [{bet['event_name']}] | Odds: {bet['bookmaker_odds']:.2f} | "
                f"Edge: {bet['edge']:.2%} | Stake: ${bet['recommended_stake_usd']:.2f} ({fraction:.2%})"
            )
            final_bets.append(bet)
            
        return final_bets

    def get_optimal_portfolio(self, df_opportunities: pd.DataFrame, max_bets: int = 5) -> pd.DataFrame:
        """
        Backward-compatible pandas interface for the historical simulator pipeline.
        """
        # Convert DataFrame to a list of dicts expected by the new professional pipeline
        opp_list = []
        for idx, row in df_opportunities.iterrows():
            opp_dict = {
                "match_id": str(row.get("match_id", idx)),
                "event_name": f"{row.get('home_team', 'Home')} vs {row.get('away_team', 'Away')}",
                "calibrated_prob": float(row.get("prob")),
                "bookmaker_odds": float(row.get("odd")),
                "pinnacle_odds": float(row.get("odd")),  # Fallback to same in simple simulations
                "event_time": pd.to_datetime(row.get("event_time", datetime.now())),
                "has_critical_injury_24h": False,
                "odds_2h_ago": float(row.get("odd")),
                "liquidity_usd": 50000.0,
                "min_liquidity_required": 1000.0,
                "historical_roi_positive": True
            }
            opp_list.append(opp_dict)
            
        final_bets = self.optimize_daily_portfolio(opp_list)
        
        if not final_bets:
            return pd.DataFrame()
            
        # Re-convert back to a formatted pandas DataFrame for the backtester
        df_out = pd.DataFrame(final_bets)
        # Map fields back to what backtester expects
        df_out["recommended_stake"] = df_out["final_kelly_fraction"]
        return df_out.head(max_bets)
