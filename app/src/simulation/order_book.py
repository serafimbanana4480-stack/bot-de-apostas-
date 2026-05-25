"""Order book simulator for realistic betting market simulation.

This module provides a simulation of a betting exchange order book with
multiple depth levels, slippage modeling, and market impact estimation.
It is designed to model realistic fill dynamics for football and basketball
betting markets where liquidity can vary significantly across price levels.

Typical usage:
    >>> simulator = OrderBookSimulator()
    >>> book = simulator.generate_book(mid_price=1.95, liquidity=50000.0, volatility=0.15)
    >>> fill = simulator.simulate_fill(side="back", stake=500.0, book=book)
    >>> effective = simulator.get_effective_odds(requested_odds=1.95, stake=500.0, book=book)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger("order_book_sim")

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class OrderBookLevel:
    """A single price/size level in the order book.

    Attributes:
        price: The odds (price) at this level.
        size: The available stake (volume) at this level.
    """

    price: float
    size: float

    def is_empty(self) -> bool:
        """Return True if this level has no available size."""
        return self.size <= 0.0


@dataclass
class OrderBook:
    """Snapshot of a betting exchange order book.

    Attributes:
        bid_levels: List of bid (back) levels, ordered from best (highest) to worst.
        ask_levels: List of ask (lay) levels, ordered from best (lowest) to worst.
        timestamp: Unix timestamp when the book was captured.
    """

    bid_levels: List[OrderBookLevel]
    ask_levels: List[OrderBookLevel]
    timestamp: float = field(default_factory=time.time)

    @property
    def best_bid(self) -> Optional[float]:
        """Best available back odds (highest bid price)."""
        if self.bid_levels:
            return self.bid_levels[0].price
        return None

    @property
    def best_ask(self) -> Optional[float]:
        """Best available lay odds (lowest ask price)."""
        if self.ask_levels:
            return self.ask_levels[0].price
        return None

    @property
    def spread(self) -> Optional[float]:
        """Bid-ask spread in odds terms."""
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None

    @property
    def mid_price(self) -> Optional[float]:
        """Mid-market price (average of best bid and best ask)."""
        if self.best_bid is not None and self.best_ask is not None:
            return (self.best_bid + self.best_ask) / 2.0
        return None

    @property
    def total_bid_liquidity(self) -> float:
        """Total available stake across all bid (back) levels."""
        return sum(level.size for level in self.bid_levels)

    @property
    def total_ask_liquidity(self) -> float:
        """Total available stake across all ask (lay) levels."""
        return sum(level.size for level in self.ask_levels)


# ---------------------------------------------------------------------------
# Realistic default parameters for popular markets
# ---------------------------------------------------------------------------

# Typical liquidity (in currency units) and volatility for major markets.
MARKET_DEFAULTS: Dict[str, Dict[str, float]] = {
    "football_match_odds": {
        "base_liquidity": 100_000.0,
        "typical_volatility": 0.12,
        "typical_spread_bps": 10.0,
    },
    "football_over_under": {
        "base_liquidity": 50_000.0,
        "typical_volatility": 0.15,
        "typical_spread_bps": 15.0,
    },
    "basketball_moneyline": {
        "base_liquidity": 30_000.0,
        "typical_volatility": 0.18,
        "typical_spread_bps": 20.0,
    },
    "basketball_spread": {
        "base_liquidity": 20_000.0,
        "typical_volatility": 0.20,
        "typical_spread_bps": 25.0,
    },
    "football_both_teams_score": {
        "base_liquidity": 25_000.0,
        "typical_volatility": 0.14,
        "typical_spread_bps": 18.0,
    },
}


# ---------------------------------------------------------------------------
# OrderBookSimulator
# ---------------------------------------------------------------------------


class OrderBookSimulator:
    """Simulates a realistic betting exchange order book with depth, slippage, and impact.

    This simulator models the key micro-structure features of betting exchanges:
    - Multiple depth levels with decreasing size away from the mid price.
    - Slippage that increases as order size consumes deeper levels.
    - A quadratic market impact model calibrated to betting market data.
    - Odds movement simulation driven by order flow.

    Args:
        depth_levels: Number of price levels on each side of the book.
        impact_coefficient: Scaling factor for the quadratic market impact model.
            Higher values mean larger price impact for the same relative order size.
        base_slippage_bps: Base slippage in basis points applied even to small
            orders that fit within the top level. Represents the minimum friction.

    Example:
        >>> sim = OrderBookSimulator(depth_levels=5, impact_coefficient=0.1)
        >>> book = sim.generate_book(mid_price=2.10, liquidity=80000, volatility=0.12)
        >>> fill_result = sim.simulate_fill(side="back", stake=2000, book=book)
    """

    def __init__(
        self,
        depth_levels: int = 5,
        impact_coefficient: float = 0.1,
        base_slippage_bps: float = 5.0,
    ) -> None:
        self.depth_levels = depth_levels
        self.impact_coefficient = impact_coefficient
        self.base_slippage_bps = base_slippage_bps

        logger.info(
            "OrderBookSimulator initialized: depth_levels=%d, "
            "impact_coefficient=%.4f, base_slippage_bps=%.1f",
            self.depth_levels,
            self.impact_coefficient,
            self.base_slippage_bps,
        )

    # ------------------------------------------------------------------
    # Book generation
    # ------------------------------------------------------------------

    def generate_book(
        self,
        mid_price: float,
        liquidity: float,
        volatility: float,
    ) -> Dict:
        """Generate a realistic order book around the given mid price.

        The book is constructed with the following properties:
        - Bid (back) levels are below the mid price; ask (lay) levels are above.
        - Level spacing widens with distance from the mid price, scaled by
          volatility to reflect wider spreads in volatile markets.
        - Size at each level decreases exponentially from the inside out,
          simulating the typical concentration of liquidity near the best price.
        - A small random perturbation is applied to both prices and sizes for
          realism.

        Args:
            mid_price: The fair / mid-market odds around which to build the book.
            liquidity: Total available liquidity (in currency units) on each side.
                Higher liquidity produces larger sizes at each level.
            volatility: Market volatility estimate (0 to 1). Higher volatility
                widens the spread and level spacing.

        Returns:
            A dictionary with keys ``"order_book"`` (an :class:`OrderBook` instance)
            and ``"metadata"`` containing generation parameters.

        Raises:
            ValueError: If mid_price <= 1.0, liquidity <= 0, or volatility not in (0, 1].
        """
        if mid_price <= 1.0:
            raise ValueError(f"mid_price must be > 1.0, got {mid_price}")
        if liquidity <= 0:
            raise ValueError(f"liquidity must be > 0, got {liquidity}")
        if not (0.0 < volatility <= 1.0):
            raise ValueError(f"volatility must be in (0, 1], got {volatility}")

        rng = np.random.default_rng()

        # Spread in odds terms: higher volatility -> wider spread.
        # Typical spread for football match odds is ~1-2 ticks (0.01-0.02).
        base_spread = 0.01 + volatility * 0.02
        half_spread = base_spread / 2.0

        # Level spacing grows with distance from mid.
        # First level is at half_spread; subsequent levels widen gradually.
        bid_levels: List[OrderBookLevel] = []
        ask_levels: List[OrderBookLevel] = []

        # Size distribution: exponential decay from inside to outside.
        # The top level gets ~30% of total liquidity, second ~25%, etc.
        raw_weights = np.array([0.30, 0.25, 0.20, 0.15, 0.10][: self.depth_levels])
        if len(raw_weights) < self.depth_levels:
            # Extend with decaying weights if depth_levels > 5.
            extra = self.depth_levels - len(raw_weights)
            last = raw_weights[-1]
            for i in range(extra):
                raw_weights = np.append(raw_weights, last * (0.5 ** (i + 1)))
        weights = raw_weights / raw_weights.sum()

        for i in range(self.depth_levels):
            # Distance from mid price increases with level index.
            # Spacing grows quadratically to simulate widening book.
            distance = half_spread * (1.0 + i * (0.5 + volatility * 0.5))

            # Small random perturbation to price (+/- 5% of distance).
            price_noise = rng.normal(0, distance * 0.05)

            bid_price = round(mid_price - distance + price_noise, 4)
            ask_price = round(mid_price + distance + price_noise, 4)

            # Ensure bid prices stay above 1.01 (minimum odds on most exchanges).
            bid_price = max(bid_price, 1.01)
            ask_price = max(ask_price, bid_price + 0.01)

            # Size at this level, with random perturbation (+/- 15%).
            base_size = liquidity * weights[i]
            size_noise = rng.normal(1.0, 0.15)
            size = max(base_size * size_noise, 0.0)

            bid_levels.append(OrderBookLevel(price=bid_price, size=round(size, 2)))
            ask_levels.append(OrderBookLevel(price=ask_price, size=round(size, 2)))

        # Sort: bids descending by price (best first), asks ascending (best first).
        bid_levels.sort(key=lambda lvl: lvl.price, reverse=True)
        ask_levels.sort(key=lambda lvl: lvl.price, reverse=False)

        book = OrderBook(
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            timestamp=time.time(),
        )

        logger.debug(
            "Generated book: mid=%.4f, best_bid=%.4f, best_ask=%.4f, spread=%.4f",
            mid_price,
            book.best_bid,
            book.best_ask,
            book.spread,
        )

        return {
            "order_book": book,
            "metadata": {
                "mid_price": mid_price,
                "liquidity": liquidity,
                "volatility": volatility,
                "depth_levels": self.depth_levels,
            },
        }

    # ------------------------------------------------------------------
    # Fill simulation
    # ------------------------------------------------------------------

    def simulate_fill(
        self,
        side: str,
        stake: float,
        book: Dict,
    ) -> Dict:
        """Simulate an order execution across the order book with slippage.

        The fill is walked through the book levels, consuming available size
        at each level until the full stake is filled or the book is exhausted.

        Args:
            side: Trade direction -- ``"back"`` (buy at bid/lay prices) or
                ``"lay"`` (sell at ask/back prices). For a back bet the fill
                walks up the ask (lay) side; for a lay bet it walks down the
                bid (back) side.
            stake: The total stake (in currency units) to be matched.
            book: The order book dictionary as returned by :meth:`generate_book`.

        Returns:
            A dictionary with the following keys:
            - ``"filled_stake"``: Total stake actually filled.
            - ``"avg_price"``: Volume-weighted average odds at which the fill
              occurred (after slippage).
            - ``"slippage_bps"``: Slippage in basis points vs. the best price.
            - ``"levels_consumed"``: Number of book levels at least partially
              filled.
            - ``"fill_details"``: List of dicts with per-level fill info.
            - ``"residual_stake"``: Unfilled stake (0 if fully filled).

        Raises:
            ValueError: If side is not ``"back"`` or ``"lay"``, or stake <= 0.
        """
        if side not in ("back", "lay"):
            raise ValueError(f"side must be 'back' or 'lay', got '{side}'")
        if stake <= 0:
            raise ValueError(f"stake must be > 0, got {stake}")

        order_book: OrderBook = book["order_book"]

        # For a back bet, we match against lay (ask) levels.
        # For a lay bet, we match against back (bid) levels.
        if side == "back":
            levels = list(order_book.ask_levels)
            benchmark_price = order_book.best_ask
        else:
            levels = list(order_book.bid_levels)
            benchmark_price = order_book.best_bid

        if not levels or benchmark_price is None:
            logger.warning("Empty book on %s side; cannot fill.", side)
            return {
                "filled_stake": 0.0,
                "avg_price": 0.0,
                "slippage_bps": 0.0,
                "levels_consumed": 0,
                "fill_details": [],
                "residual_stake": stake,
            }

        remaining = stake
        total_cost = 0.0  # Sum of (stake_matched * price) for VWAP.
        total_filled = 0.0
        levels_consumed = 0
        fill_details: List[Dict] = []

        for level in levels:
            if remaining <= 0:
                break

            fillable = min(remaining, level.size)
            if fillable <= 0:
                continue

            total_cost += fillable * level.price
            total_filled += fillable
            remaining -= fillable
            levels_consumed += 1

            fill_details.append(
                {
                    "level_price": level.price,
                    "level_size": level.size,
                    "filled_at_level": fillable,
                    "residual_at_level": level.size - fillable,
                }
            )

        avg_price = total_cost / total_filled if total_filled > 0 else 0.0

        # Slippage in basis points relative to the benchmark (best) price.
        if benchmark_price > 0 and total_filled > 0:
            slippage_bps = (avg_price - benchmark_price) / benchmark_price * 10_000
            # For lay bets, slippage is negative (we get a worse, lower price).
            if side == "lay":
                slippage_bps = (benchmark_price - avg_price) / benchmark_price * 10_000
        else:
            slippage_bps = 0.0

        slippage_bps = abs(slippage_bps)

        logger.info(
            "Fill result: side=%s, stake=%.2f, filled=%.2f, avg_price=%.4f, "
            "slippage_bps=%.2f, levels=%d, residual=%.2f",
            side,
            stake,
            total_filled,
            avg_price,
            slippage_bps,
            levels_consumed,
            remaining,
        )

        return {
            "filled_stake": round(total_filled, 2),
            "avg_price": round(avg_price, 4),
            "slippage_bps": round(slippage_bps, 2),
            "levels_consumed": levels_consumed,
            "fill_details": fill_details,
            "residual_stake": round(remaining, 2),
        }

    # ------------------------------------------------------------------
    # Market impact
    # ------------------------------------------------------------------

    def compute_market_impact(
        self,
        stake: float,
        liquidity: float,
    ) -> float:
        """Compute the expected market impact using a quadratic model.

        The model follows the square-root / quadratic impact framework
        commonly used in market micro-structure literature, adapted for
        betting markets:

            impact = impact_coefficient * (stake / liquidity) ^ 2

        This captures the empirical observation that price impact grows
        non-linearly with order size relative to available liquidity.

        Args:
            stake: The order size in currency units.
            liquidity: The total available liquidity on the relevant side
                of the book in currency units.

        Returns:
            The expected market impact as a decimal fraction of the current
            price. For example, 0.005 means a 0.5% expected price move.

        Raises:
            ValueError: If stake <= 0 or liquidity <= 0.
        """
        if stake <= 0:
            raise ValueError(f"stake must be > 0, got {stake}")
        if liquidity <= 0:
            raise ValueError(f"liquidity must be > 0, got {liquidity}")

        participation_rate = stake / liquidity
        impact = self.impact_coefficient * (participation_rate ** 2)

        logger.debug(
            "Market impact: stake=%.2f, liquidity=%.2f, "
            "participation_rate=%.4f, impact=%.6f",
            stake,
            liquidity,
            participation_rate,
            impact,
        )

        return impact

    # ------------------------------------------------------------------
    # Slippage
    # ------------------------------------------------------------------

    def compute_slippage(
        self,
        stake: float,
        book: Dict,
    ) -> float:
        """Compute expected slippage for a given stake against the book.

        Slippage is calculated by walking through the book levels and
        computing the volume-weighted average price deviation from the
        best available price. A base slippage (``base_slippage_bps``) is
        added to account for minimum friction even on small orders.

        Args:
            stake: The order size in currency units.
            book: The order book dictionary as returned by :meth:`generate_book`.

        Returns:
            Expected slippage in basis points (bps). One basis point = 0.01%.
            For example, 5.0 bps means the effective price deviates by 0.05%
            from the best price.
        """
        order_book: OrderBook = book["order_book"]

        if not order_book.ask_levels or not order_book.bid_levels:
            return self.base_slippage_bps

        best_ask = order_book.best_ask
        if best_ask is None:
            return self.base_slippage_bps

        remaining = stake
        total_cost = 0.0
        total_filled = 0.0

        for level in order_book.ask_levels:
            if remaining <= 0:
                break
            fillable = min(remaining, level.size)
            if fillable <= 0:
                continue
            total_cost += fillable * level.price
            total_filled += fillable
            remaining -= fillable

        if total_filled > 0 and best_ask > 0:
            vwap = total_cost / total_filled
            raw_slippage = (vwap - best_ask) / best_ask * 10_000
        else:
            raw_slippage = 0.0

        # Add base slippage (minimum friction).
        total_slippage = abs(raw_slippage) + self.base_slippage_bps

        logger.debug(
            "Slippage: stake=%.2f, vwap=%.4f, best_ask=%.4f, "
            "raw_slippage=%.2f bps, total=%.2f bps",
            stake,
            total_cost / total_filled if total_filled > 0 else 0.0,
            best_ask,
            raw_slippage,
            total_slippage,
        )

        return round(total_slippage, 2)

    # ------------------------------------------------------------------
    # Odds movement
    # ------------------------------------------------------------------

    def simulate_odds_movement(
        self,
        current_odds: float,
        volume: float,
        direction: str,
    ) -> float:
        """Simulate how odds move after a large bet is placed.

        When a large back bet is placed, the lay side is consumed and odds
        typically shorten (decrease). When a large lay bet is placed, the
        back side is consumed and odds typically drift (increase).

        The movement magnitude is proportional to the market impact and
        includes a stochastic component to simulate real market noise.

        Args:
            current_odds: The current mid-market odds.
            volume: The volume (stake) of the bet driving the movement.
            direction: ``"shorten"`` (odds decrease, e.g. after large back
                bets) or ``"drift"`` (odds increase, e.g. after large lay
                bets).

        Returns:
            The new odds after the simulated movement, rounded to 2 decimal
            places (typical exchange tick precision).

        Raises:
            ValueError: If current_odds <= 1.0, volume <= 0, or direction
                is not ``"shorten"`` or ``"drift"``.
        """
        if current_odds <= 1.0:
            raise ValueError(f"current_odds must be > 1.0, got {current_odds}")
        if volume <= 0:
            raise ValueError(f"volume must be > 0, got {volume}")
        if direction not in ("shorten", "drift"):
            raise ValueError(
                f"direction must be 'shorten' or 'drift', got '{direction}'"
            )

        # Estimate liquidity from the current odds using a heuristic:
        # higher odds imply lower implied probability and typically lower liquidity.
        implied_prob = 1.0 / current_odds
        estimated_liquidity = 50_000.0 * implied_prob  # More liquid for favourites.

        impact = self.compute_market_impact(volume, estimated_liquidity)

        # Directional movement.
        movement = current_odds * impact

        # Add stochastic noise proportional to impact.
        rng = np.random.default_rng()
        noise = rng.normal(0, movement * 0.3)

        if direction == "shorten":
            new_odds = current_odds - movement + noise
        else:  # drift
            new_odds = current_odds + movement + noise

        # Odds cannot go below 1.01 (exchange minimum).
        new_odds = max(round(new_odds, 2), 1.01)

        logger.debug(
            "Odds movement: current=%.4f, volume=%.2f, direction=%s, "
            "impact=%.6f, new_odds=%.4f",
            current_odds,
            volume,
            direction,
            impact,
            new_odds,
        )

        return new_odds

    # ------------------------------------------------------------------
    # Effective odds
    # ------------------------------------------------------------------

    def get_effective_odds(
        self,
        requested_odds: float,
        stake: float,
        book: Dict,
    ) -> float:
        """Return the effective odds after accounting for slippage.

        This is the odds a bettor actually receives when placing an order
        at the requested odds, factoring in the slippage incurred by
        consuming multiple book levels.

        Args:
            requested_odds: The odds at which the bettor wishes to place
                the bet (typically the best available price).
            stake: The stake amount in currency units.
            book: The order book dictionary as returned by :meth:`generate_book`.

        Returns:
            The effective (volume-weighted average) odds after slippage.
            This will always be worse (lower for back bets, higher for lay
            bets) than the requested odds when slippage > 0.
        """
        slippage_bps = self.compute_slippage(stake, book)

        # Convert bps slippage to a price adjustment.
        # For a back bet, effective odds = requested * (1 - slippage/10000).
        # This represents getting a worse price than requested.
        slippage_fraction = slippage_bps / 10_000.0
        effective_odds = requested_odds * (1.0 - slippage_fraction)

        # Odds floor at 1.01.
        effective_odds = max(round(effective_odds, 4), 1.01)

        logger.debug(
            "Effective odds: requested=%.4f, stake=%.2f, "
            "slippage_bps=%.2f, effective=%.4f",
            requested_odds,
            stake,
            slippage_bps,
            effective_odds,
        )

        return effective_odds

    # ------------------------------------------------------------------
    # Fill probability
    # ------------------------------------------------------------------

    def estimate_fill_probability(
        self,
        odds: float,
        stake: float,
        book: Dict,
    ) -> float:
        """Estimate the probability of a full fill at the requested odds.

        The fill probability depends on:
        - How much liquidity is available at or better than the requested odds.
        - The ratio of the stake to the available liquidity at those levels.
        - A decay factor for levels further from the best price, as those
          levels are more likely to be cancelled or refreshed before the
          order is matched.

        Args:
            odds: The requested odds for the bet.
            stake: The stake amount in currency units.
            book: The order book dictionary as returned by :meth:`generate_book`.

        Returns:
            A float between 0.0 and 1.0 representing the probability of
            receiving a full fill at the requested odds. A value of 1.0
            means the available liquidity at or better than the requested
            odds exceeds the stake by a comfortable margin.
        """
        order_book: OrderBook = book["order_book"]

        # Determine which side of the book to examine.
        # If requested odds >= best_ask, we look at ask (lay) side for a back bet.
        # If requested odds <= best_bid, we look at bid (back) side for a lay bet.
        best_bid = order_book.best_bid
        best_ask = order_book.best_ask

        if best_ask is not None and odds >= best_ask:
            # Back bet: check ask (lay) side.
            relevant_levels = order_book.ask_levels
            # Only consider levels at or below the requested odds.
            matching_levels = [lvl for lvl in relevant_levels if lvl.price <= odds]
        elif best_bid is not None and odds <= best_bid:
            # Lay bet: check bid (back) side.
            relevant_levels = order_book.bid_levels
            # Only consider levels at or above the requested odds.
            matching_levels = [lvl for lvl in relevant_levels if lvl.price >= odds]
        else:
            # Odds are inside the spread -- very unlikely to fill.
            logger.debug(
                "Fill probability: odds=%.4f inside spread (bid=%.4f, ask=%.4f), p=0.05",
                odds,
                best_bid,
                best_ask,
            )
            return 0.05

        if not matching_levels:
            return 0.0

        # Available liquidity at matching levels, with a decay factor
        # for deeper levels (they are less reliable).
        total_effective_liquidity = 0.0
        for i, level in enumerate(matching_levels):
            # Decay factor: level 0 = 100%, level 1 = 90%, level 2 = 80%, etc.
            decay = max(1.0 - i * 0.10, 0.1)
            total_effective_liquidity += level.size * decay

        if total_effective_liquidity <= 0:
            return 0.0

        # Fill probability based on the ratio of available liquidity to stake.
        # Using a logistic-style function for smooth probability curve.
        ratio = total_effective_liquidity / stake
        # Sigmoid centered at ratio=1.0 with steepness=3.
        probability = 1.0 / (1.0 + np.exp(-3.0 * (ratio - 1.0)))

        # Cap at [0, 1].
        probability = float(np.clip(probability, 0.0, 1.0))

        logger.debug(
            "Fill probability: odds=%.4f, stake=%.2f, "
            "effective_liquidity=%.2f, ratio=%.2f, probability=%.4f",
            odds,
            stake,
            total_effective_liquidity,
            ratio,
            probability,
        )

        return probability
