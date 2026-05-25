"""
Dynamic slippage model for betting execution simulation.

Models slippage as a function of:
- Stake size relative to available liquidity
- Time to kickoff (slippage increases near event start)
- Market regime (higher slippage in volatile/illiquid markets)
- Bet side (back vs lay may have different depth profiles)

Usage:
    from src.simulations.slippage_model import SlippageModel

    model = SlippageModel()
    slippage = model.compute(
        stake=100.0,
        available_liquidity=5000.0,
        hours_to_kickoff=3.0,
        regime="high_vol",
        best_price=2.10,
    )
    # slippage.effective_price, slippage.bps, etc.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger("slippage_model")


@dataclass
class SlippageEstimate:
    """Result of a slippage computation."""
    requested_price: float      # Best available price
    effective_price: float      # Price after slippage
    slippage_bps: float         # Slippage in basis points
    slippage_pct: float         # Slippage as percentage
    stake_fraction_filled: float  # Fraction of stake that can be filled
    regime_factor: float        # Regime multiplier applied
    time_factor: float          # Time-to-kickoff multiplier applied
    liquidity_factor: float    # Liquidity ratio (stake/available)


# Regime-dependent slippage multipliers
REGIME_SLIPPAGE_FACTORS: dict[str, float] = {
    "low_vol": 0.7,      # Lower slippage in calm markets
    "normal": 1.0,        # Baseline
    "high_vol": 1.8,      # Higher slippage in volatile markets
    "illiquid": 2.5,      # Very high slippage in thin markets
}

# Time-to-kickoff slippage curve coefficients
# Slippage increases as kickoff approaches (less time for market to absorb)
TIME_SLIPPAGE_COEFFICIENTS = {
    "base": 1.0,
    "urgency_slope": 0.3,    # Additional slippage per hour closer to kickoff
    "min_hours": 0.5,        # Minimum hours (very close to kickoff)
    "max_multiplier": 3.0,   # Cap on time-based multiplier
}


class SlippageModel:
    """
    Dynamic slippage model for betting execution.

    Combines three factors to estimate execution slippage:
    1. Liquidity factor: stake / available_liquidity (base slippage)
    2. Time factor: increases as kickoff approaches
    3. Regime factor: adjusts for market conditions

    The model assumes slippage is proportional to the square root of
    the stake-to-liquidity ratio (square-root market impact law),
    scaled by time and regime factors.

    Args:
        base_slippage_bps: Base slippage in bps at 1% liquidity consumption
        max_slippage_bps: Maximum allowed slippage (circuit breaker)
        min_fill_fraction: Minimum fraction of stake that must be fillable
    """

    def __init__(
        self,
        base_slippage_bps: float = 5.0,
        max_slippage_bps: float = 200.0,
        min_fill_fraction: float = 0.5,
    ):
        self.base_slippage_bps = base_slippage_bps
        self.max_slippage_bps = max_slippage_bps
        self.min_fill_fraction = min_fill_fraction

    def compute(
        self,
        stake: float,
        available_liquidity: float,
        hours_to_kickoff: float = 6.0,
        regime: str = "normal",
        best_price: float = 2.0,
        side: str = "back",
    ) -> SlippageEstimate:
        """
        Compute slippage estimate for a potential bet.

        Args:
            stake: Bet size in currency units
            available_liquidity: Total available volume at best price levels
            hours_to_kickoff: Hours until event start
            regime: Market regime ("low_vol", "normal", "high_vol", "illiquid")
            best_price: Best available odds
            side: "back" or "lay"

        Returns:
            SlippageEstimate with effective price and slippage details.
        """
        if stake <= 0 or available_liquidity <= 0 or best_price <= 1.0:
            return SlippageEstimate(
                requested_price=best_price,
                effective_price=best_price,
                slippage_bps=0.0,
                slippage_pct=0.0,
                stake_fraction_filled=0.0,
                regime_factor=1.0,
                time_factor=1.0,
                liquidity_factor=0.0,
            )

        # --- 1. Liquidity factor ---
        # Square-root impact law: slippage ~ sqrt(stake / liquidity)
        liquidity_ratio = stake / available_liquidity
        liquidity_factor = min(liquidity_ratio, 1.0)

        # Base slippage scales with sqrt of liquidity consumption
        base_slip = self.base_slippage_bps * np.sqrt(liquidity_ratio)

        # --- 2. Time factor ---
        # Slippage increases as kickoff approaches
        hours = max(hours_to_kickoff, TIME_SLIPPAGE_COEFFICIENTS["min_hours"])
        time_multiplier = 1.0 + TIME_SLIPPAGE_COEFFICIENTS["urgency_slope"] / hours
        time_multiplier = min(time_multiplier, TIME_SLIPPAGE_COEFFICIENTS["max_multiplier"])

        # --- 3. Regime factor ---
        regime_factor = REGIME_SLIPPAGE_FACTORS.get(regime, 1.0)

        # --- Combined slippage ---
        total_slippage_bps = base_slip * time_multiplier * regime_factor
        total_slippage_bps = min(total_slippage_bps, self.max_slippage_bps)

        # Convert to price impact
        slippage_pct = total_slippage_bps / 10000.0

        # Effective price (worse for bettor)
        if side.lower() == "back":
            # Backing: slippage makes odds worse (lower)
            effective_price = best_price * (1 - slippage_pct)
            effective_price = max(1.01, effective_price)
        else:
            # Laying: slippage makes odds worse (higher)
            effective_price = best_price * (1 + slippage_pct)

        # Fill fraction: how much of the stake can be filled at effective price
        fill_fraction = min(1.0, available_liquidity / stake) if stake > 0 else 0.0
        fill_fraction = max(fill_fraction, self.min_fill_fraction)

        return SlippageEstimate(
            requested_price=best_price,
            effective_price=round(effective_price, 4),
            slippage_bps=round(total_slippage_bps, 2),
            slippage_pct=round(slippage_pct, 6),
            stake_fraction_filled=round(fill_fraction, 4),
            regime_factor=regime_factor,
            time_factor=round(time_multiplier, 4),
            liquidity_factor=round(liquidity_factor, 4),
        )

    def should_execute(self, estimate: SlippageEstimate) -> bool:
        """
        Decide whether a bet should be executed given its slippage estimate.

        Rejects bets with:
        - Slippage exceeding max_slippage_bps
        - Fill fraction below min_fill_fraction
        """
        if estimate.slippage_bps > self.max_slippage_bps:
            logger.info(
                "Rejecting execution: slippage %.1f bps exceeds max %.1f bps",
                estimate.slippage_bps, self.max_slippage_bps,
            )
            return False

        if estimate.stake_fraction_filled < self.min_fill_fraction:
            logger.info(
                "Rejecting execution: fill fraction %.2f below min %.2f",
                estimate.stake_fraction_filled, self.min_fill_fraction,
            )
            return False

        return True

    def batch_compute(
        self,
        stakes: list,
        liquidities: list,
        hours: list,
        regimes: list,
        best_prices: list,
        sides: list | None = None,
    ) -> list:
        """Compute slippage for a batch of bets."""
        sides = sides or ["back"] * len(stakes)
        results = []
        for s, l, h, r, p, side in zip(stakes, liquidities, hours, regimes, best_prices, sides):
            results.append(self.compute(s, l, h, r, p, side))
        return results
