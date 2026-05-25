"""
Simulated order book with depth levels for realistic execution modelling.

Models top N price levels per side (back/lay) with available volume,
market impact (quadratic model), and time/regime-dependent slippage.

Usage:
    from src.simulations.order_book import OrderBookSimulator

    ob = OrderBookSimulator(
        initial_odds=2.10,
        total_liquidity=5000.0,
        n_levels=5,
    )
    depth = ob.get_depth("back")
    fill = ob.simulate_fill(stake=100.0, side="back")
    impact = ob.market_impact(stake=200.0)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger("order_book")


@dataclass
class OrderBookLevel:
    """Single price level in the order book."""
    price: float       # Decimal odds
    volume: float      # Available stake at this level
    side: str          # "back" or "lay"


@dataclass
class FillResult:
    """Result of a simulated order execution."""
    requested_stake: float
    filled_stake: float
    avg_fill_price: float
    slippage_bps: float       # Basis points of slippage vs best price
    levels_used: int          # How many depth levels were consumed
    partial_fill: bool        # True if not fully filled
    price_impact: float       # Price movement caused by this fill
    details: list[dict[str, Any]] = field(default_factory=list)


class OrderBookSimulator:
    """
    Simulated order book with configurable depth levels.

    Generates a realistic order book from initial odds and total liquidity,
    modelling:
    - Top N back/lay levels with decreasing volume at worse prices
    - Quadratic market impact: delta = alpha * (stake / liquidity)^2
    - Time-dependent slippage (increases near kickoff)
    - Regime-dependent depth (thinner in volatile/low-liquidity markets)
    - Partial fills when stake exceeds available depth

    Args:
        initial_odds: Mid-price odds (e.g. 2.10)
        total_liquidity: Total available volume across all levels (in currency)
        n_levels: Number of depth levels per side
        spread_bps: Bid-ask spread in basis points (default 50 = 0.5%)
        depth_decay: Volume decay factor per level (0.6 = 60% of previous)
        impact_alpha: Market impact coefficient for quadratic model
        seed: Random seed for reproducibility
    """

    def __init__(
        self,
        initial_odds: float = 2.10,
        total_liquidity: float = 5000.0,
        n_levels: int = 5,
        spread_bps: float = 50.0,
        depth_decay: float = 0.6,
        impact_alpha: float = 0.5,
        seed: int | None = None,
    ):
        if initial_odds <= 1.0:
            raise ValueError(f"initial_odds must be > 1.0, got {initial_odds}")
        if total_liquidity <= 0:
            raise ValueError(f"total_liquidity must be > 0, got {total_liquidity}")

        self.initial_odds = initial_odds
        self.total_liquidity = total_liquidity
        self.n_levels = n_levels
        self.spread_bps = spread_bps
        self.depth_decay = depth_decay
        self.impact_alpha = impact_alpha

        self._rng = np.random.RandomState(seed)
        self._back_levels: list[OrderBookLevel] = []
        self._lay_levels: list[OrderBookLevel] = []
        self._build_book()

    def _build_book(self) -> None:
        """Construct the order book from initial parameters."""
        mid = self.initial_odds
        half_spread = mid * (self.spread_bps / 10000.0) / 2.0

        best_back = mid - half_spread   # Best price to back (lower = better for bettor)
        best_lay = mid + half_spread    # Best price to lay (higher = better for layer)

        # Distribute liquidity across levels using geometric decay
        back_volumes = self._distribute_volume(self.total_liquidity * 0.5, self.n_levels)
        lay_volumes = self._distribute_volume(self.total_liquidity * 0.5, self.n_levels)

        # Price step increases with level (worse prices deeper in the book)
        self._back_levels = []
        self._lay_levels = []

        for i in range(self.n_levels):
            # Back side: prices decrease (worse for bettor) as we go deeper
            back_price_step = half_spread * (1 + i * 0.5)
            back_price = max(1.01, best_back - back_price_step * i)
            self._back_levels.append(OrderBookLevel(
                price=round(back_price, 4),
                volume=back_volumes[i],
                side="back",
            ))

            # Lay side: prices increase (worse for layer) as we go deeper
            lay_price_step = half_spread * (1 + i * 0.5)
            lay_price = best_lay + lay_price_step * i
            self._lay_levels.append(OrderBookLevel(
                price=round(lay_price, 4),
                volume=lay_volumes[i],
                side="lay",
            ))

    def _distribute_volume(self, total: float, n_levels: int) -> list[float]:
        """Distribute total volume across levels with geometric decay."""
        if self.depth_decay <= 0 or self.depth_decay >= 1:
            # Equal distribution
            per_level = total / n_levels
            return [per_level] * n_levels

        # Geometric series: a * (1 - r^n) / (1 - r) = total
        # a = total * (1 - r) / (1 - r^n)
        r = self.depth_decay
        a = total * (1 - r) / (1 - r ** n_levels)
        return [a * (r ** i) for i in range(n_levels)]

    def get_depth(self, side: str) -> list[OrderBookLevel]:
        """
        Return order book depth for back or lay side.

        Args:
            side: "back" or "lay"

        Returns:
            List of OrderBookLevel ordered from best to worst price.
        """
        if side.lower() == "back":
            return list(self._back_levels)
        elif side.lower() == "lay":
            return list(self._lay_levels)
        else:
            raise ValueError(f"side must be 'back' or 'lay', got '{side}'")

    def get_best_price(self, side: str) -> float:
        """Get the best available price for a side."""
        levels = self.get_depth(side)
        return levels[0].price if levels else self.initial_odds

    def get_available_volume(self, side: str) -> float:
        """Get total available volume across all levels for a side."""
        return sum(level.volume for level in self.get_depth(side))

    def simulate_fill(
        self,
        stake: float,
        side: str,
        hours_to_kickoff: float = 6.0,
        regime_volatility: float = 0.1,
    ) -> FillResult:
        """
        Simulate order execution with slippage across depth levels.

        Walks through the order book levels, consuming volume at each level
        until the full stake is filled or the book is exhausted.

        Args:
            stake: Amount to bet (in currency units)
            side: "back" or "lay"
            hours_to_kickoff: Time until event start (affects slippage)
            regime_volatility: Current market volatility (0-1, affects depth)

        Returns:
            FillResult with execution details including slippage and impact.
        """
        if stake <= 0:
            return FillResult(
                requested_stake=stake, filled_stake=0.0,
                avg_fill_price=self.get_best_price(side),
                slippage_bps=0.0, levels_used=0,
                partial_fill=True, price_impact=0.0,
            )

        levels = self.get_depth(side)
        if not levels:
            return FillResult(
                requested_stake=stake, filled_stake=0.0,
                avg_fill_price=self.initial_odds,
                slippage_bps=0.0, levels_used=0,
                partial_fill=True, price_impact=0.0,
            )

        # Apply regime-dependent depth scaling
        # In high volatility, effective volume is reduced
        depth_scale = max(0.3, 1.0 - regime_volatility * 0.5)

        # Apply time-dependent depth scaling
        # Closer to kickoff = less available depth
        time_scale = min(1.0, max(0.2, hours_to_kickoff / 12.0))

        effective_scale = depth_scale * time_scale

        remaining = stake
        total_cost = 0.0
        levels_used = 0
        details: list[dict[str, Any]] = []
        best_price = levels[0].price

        for level in levels:
            if remaining <= 0:
                break

            available = level.volume * effective_scale
            take = min(remaining, available)

            if take <= 0:
                continue

            # Cost of taking this level: stake / odds (for back) or stake * (odds - 1) (for lay)
            level_cost = take  # Currency amount wagered at this level
            total_cost += level_cost * level.price  # Total return if win
            remaining -= take
            levels_used += 1

            details.append({
                "price": level.price,
                "volume_taken": take,
                "volume_available": available,
            })

        filled = stake - remaining
        partial = remaining > 1e-6

        # Weighted average fill price
        if filled > 0 and total_cost > 0:
            avg_price = total_cost / filled
        else:
            avg_price = best_price

        # Slippage in basis points vs best available price
        if best_price > 0:
            slippage_bps = abs(avg_price - best_price) / best_price * 10000
        else:
            slippage_bps = 0.0

        # Market impact from this fill
        impact = self.market_impact(stake)

        return FillResult(
            requested_stake=stake,
            filled_stake=filled,
            avg_fill_price=round(avg_price, 4),
            slippage_bps=round(slippage_bps, 2),
            levels_used=levels_used,
            partial_fill=partial,
            price_impact=round(impact, 6),
            details=details,
        )

    def market_impact(self, stake: float) -> float:
        """
        Quadratic market impact model.

        price_move = alpha * (stake / available_liquidity)^2

        This models the fact that larger bets move the market more
        than proportionally (convex impact).

        Args:
            stake: Bet size in currency units

        Returns:
            Expected price movement (as a fraction, e.g. 0.01 = 1%)
        """
        available = self.get_available_volume("back")
        if available <= 0:
            return 0.0

        ratio = stake / available
        return self.impact_alpha * ratio * ratio

    def update_prices(self, market_move: float) -> None:
        """
        Shift all prices by a percentage (simulating market movement).

        Args:
            market_move: Fractional price change (e.g. -0.05 = -5%)
        """
        for level in self._back_levels:
            level.price = max(1.01, round(level.price * (1 + market_move), 4))
        for level in self._lay_levels:
            level.price = max(1.01, round(level.price * (1 + market_move), 4))

    def refresh_liquidity(self, total_liquidity: float) -> None:
        """
        Refresh the order book with new total liquidity.

        Simulates new liquidity entering the market.
        """
        self.total_liquidity = total_liquidity
        self._build_book()

    def to_dict(self) -> dict[str, Any]:
        """Serialize order book state to dict."""
        return {
            "initial_odds": self.initial_odds,
            "total_liquidity": self.total_liquidity,
            "n_levels": self.n_levels,
            "spread_bps": self.spread_bps,
            "best_back": self.get_best_price("back"),
            "best_lay": self.get_best_price("lay"),
            "back_volume": self.get_available_volume("back"),
            "lay_volume": self.get_available_volume("lay"),
            "back_levels": [
                {"price": l.price, "volume": l.volume} for l in self._back_levels
            ],
            "lay_levels": [
                {"price": l.price, "volume": l.volume} for l in self._lay_levels
            ],
        }
