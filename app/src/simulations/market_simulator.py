"""
Market simulator with order book depth, realistic slippage, and news shocks.

Generates synthetic dynamic betting markets with:
- Pre-game odds fluctuations (random walk + jumps)
- Order book depth at multiple price levels
- Dynamic slippage based on liquidity, time, and regime
- News events and liquidity shocks
- Steam movements (coordinated market moves)

Usage:
    from src.simulations.market_simulator import MarketSimulator

    sim = MarketSimulator(seed=42)
    trajectory = sim.simulate_odds_trajectory(
        initial_odds=2.10, hours_to_kickoff=12,
    )
    book = sim.get_order_book(step=10)
    fill = sim.simulate_execution(stake=100.0, step=10, side="back")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.simulations.order_book import FillResult, OrderBookSimulator
from src.simulations.slippage_model import SlippageEstimate, SlippageModel

logger = logging.getLogger("market_simulator")


@dataclass
class MarketStep:
    """State of the market at a single time step."""
    step: int
    hours_to_kickoff: float
    mid_odds: float
    best_back: float
    best_lay: float
    back_volume: float
    lay_volume: float
    spread_bps: float
    regime: str  # "low_vol", "normal", "high_vol"
    event: str   # "none", "news", "steam", "liquidity_shock"


class MarketSimulator:
    """
    Generates synthetic dynamic betting markets with order book depth.

    Simulates pre-game odds fluctuations, news events, steam movements,
    and liquidity shocks, with full order book at each time step.

    Args:
        seed: Random seed for reproducibility
        n_levels: Number of order book depth levels per side
        base_liquidity: Default total liquidity in currency units
        slippage_model: Optional custom SlippageModel instance
    """

    def __init__(
        self,
        seed: int = 42,
        n_levels: int = 5,
        base_liquidity: float = 5000.0,
        slippage_model: SlippageModel | None = None,
    ):
        self._rng = np.random.RandomState(seed)
        self.n_levels = n_levels
        self.base_liquidity = base_liquidity
        self.slippage_model = slippage_model or SlippageModel()

        # Trajectory state (populated after simulate_odds_trajectory)
        self._trajectory: list[float] = []
        self._steps: list[MarketStep] = []
        self._order_books: list[OrderBookSimulator] = []

    def simulate_odds_trajectory(
        self,
        initial_odds: float,
        hours_to_kickoff: int = 12,
        steps_per_hour: int = 2,
        news_event_prob: float = 0.05,
        steam_prob: float = 0.02,
        liquidity_shock_prob: float = 0.01,
    ) -> list[float]:
        """
        Simulate odds movement with order book at each step.

        Extends the basic random walk with:
        - News shocks (sudden large moves)
        - Steam movements (coordinated directional moves)
        - Liquidity shocks (sudden volume changes)
        - Regime detection at each step

        Args:
            initial_odds: Starting odds value
            hours_to_kickoff: Hours until event start
            steps_per_hour: Simulation granularity
            news_event_prob: Probability of a news shock per step
            steam_prob: Probability of a steam move per step
            liquidity_shock_prob: Probability of a liquidity shock per step

        Returns:
            List of mid-price odds at each time step.
        """
        total_steps = hours_to_kickoff * steps_per_hour
        odds_series = [initial_odds]
        current_odds = initial_odds

        # Reset state
        self._trajectory = [initial_odds]
        self._steps = []
        self._order_books = []

        # Initial liquidity (may vary with odds)
        current_liquidity = self.base_liquidity

        for step in range(total_steps):
            hours_left = hours_to_kickoff - (step / steps_per_hour)
            event = "none"

            # --- Normal fluctuation ---
            # Variance increases closer to kickoff
            volatility = 0.01 * (1.0 / max(0.5, hours_left))
            change_pct = self._rng.normal(0, volatility)

            # --- News shock ---
            if self._rng.rand() < news_event_prob:
                jump = self._rng.choice([-1.0, 1.0]) * self._rng.uniform(0.08, 0.15)
                change_pct += jump
                event = "news"
                # News events often reduce liquidity temporarily
                current_liquidity *= self._rng.uniform(0.5, 0.8)

            # --- Steam movement ---
            if self._rng.rand() < steam_prob:
                # Coordinated move in one direction (smart money)
                steam_dir = self._rng.choice([-1.0, 1.0])
                steam_size = self._rng.uniform(0.03, 0.08)
                change_pct += steam_dir * steam_size
                event = "steam"

            # --- Liquidity shock ---
            if self._rng.rand() < liquidity_shock_prob:
                shock_factor = self._rng.uniform(0.3, 0.6)
                current_liquidity *= shock_factor
                event = "liquidity_shock"
                logger.debug("Liquidity shock at step %d: %.1f%% remaining", step, shock_factor * 100)

            # Apply change
            current_odds = current_odds * (1.0 + change_pct)
            current_odds = max(1.01, min(100.0, current_odds))

            # Liquidity slowly recovers
            current_liquidity = min(
                self.base_liquidity,
                current_liquidity * 1.02,  # 2% recovery per step
            )

            # Detect regime
            regime = self._detect_regime(volatility, current_liquidity)

            # Build order book for this step
            spread_bps = 50.0 + (30.0 if regime == "high_vol" else 0.0)
            ob = OrderBookSimulator(
                initial_odds=current_odds,
                total_liquidity=current_liquidity,
                n_levels=self.n_levels,
                spread_bps=spread_bps,
                seed=step,  # Different seed per step for variety
            )

            # Record step
            market_step = MarketStep(
                step=step,
                hours_to_kickoff=hours_left,
                mid_odds=current_odds,
                best_back=ob.get_best_price("back"),
                best_lay=ob.get_best_price("lay"),
                back_volume=ob.get_available_volume("back"),
                lay_volume=ob.get_available_volume("lay"),
                spread_bps=spread_bps,
                regime=regime,
                event=event,
            )
            self._steps.append(market_step)
            self._order_books.append(ob)
            self._trajectory.append(current_odds)
            odds_series.append(float(current_odds))

        return odds_series

    def _detect_regime(self, volatility: float, liquidity: float) -> str:
        """Detect market regime from volatility and liquidity."""
        if volatility > 0.03 or liquidity < self.base_liquidity * 0.3:
            return "high_vol"
        elif volatility < 0.008 and liquidity > self.base_liquidity * 0.7:
            return "low_vol"
        return "normal"

    def get_order_book(self, step: int) -> OrderBookSimulator | None:
        """Get the order book at a specific simulation step."""
        if 0 <= step < len(self._order_books):
            return self._order_books[step]
        return None

    def get_step(self, step: int) -> MarketStep | None:
        """Get market state at a specific step."""
        if 0 <= step < len(self._steps):
            return self._steps[step]
        return None

    def simulate_execution(
        self,
        stake: float,
        step: int,
        side: str = "back",
    ) -> FillResult | None:
        """
        Simulate a bet execution at a specific time step.

        Uses the order book at the given step to simulate fill with slippage.

        Args:
            stake: Bet size in currency units
            step: Simulation step index
            side: "back" or "lay"

        Returns:
            FillResult or None if step is out of range.
        """
        ob = self.get_order_book(step)
        if ob is None:
            return None

        market_step = self.get_step(step)
        hours = market_step.hours_to_kickoff if market_step else 6.0
        regime = market_step.regime if market_step else "normal"
        vol = 0.1 if regime == "high_vol" else (0.02 if regime == "low_vol" else 0.05)

        return ob.simulate_fill(
            stake=stake,
            side=side,
            hours_to_kickoff=hours,
            regime_volatility=vol,
        )

    def compute_slippage(
        self,
        stake: float,
        step: int,
        side: str = "back",
    ) -> SlippageEstimate | None:
        """
        Compute slippage estimate for a potential bet at a given step.

        Uses the SlippageModel with market conditions at the step.
        """
        market_step = self.get_step(step)
        if market_step is None:
            return None

        return self.slippage_model.compute(
            stake=stake,
            available_liquidity=market_step.back_volume if side == "back" else market_step.lay_volume,
            hours_to_kickoff=market_step.hours_to_kickoff,
            regime=market_step.regime,
            best_price=market_step.best_back if side == "back" else market_step.best_lay,
            side=side,
        )

    @property
    def trajectory(self) -> list[float]:
        """Get the full odds trajectory."""
        return list(self._trajectory)

    @property
    def steps(self) -> list[MarketStep]:
        """Get all market step records."""
        return list(self._steps)

    def summary(self) -> dict[str, Any]:
        """Get a summary of the simulation."""
        if not self._steps:
            return {"status": "no_simulation"}

        regimes = [s.regime for s in self._steps]
        events = [s.event for s in self._steps if s.event != "none"]

        return {
            "total_steps": len(self._steps),
            "initial_odds": self._trajectory[0],
            "final_odds": self._trajectory[-1],
            "odds_change_pct": (self._trajectory[-1] / self._trajectory[0] - 1) * 100,
            "regime_distribution": {
                "low_vol": regimes.count("low_vol"),
                "normal": regimes.count("normal"),
                "high_vol": regimes.count("high_vol"),
            },
            "events": {
                "news": events.count("news"),
                "steam": events.count("steam"),
                "liquidity_shock": events.count("liquidity_shock"),
            },
            "avg_liquidity": float(np.mean([s.back_volume + s.lay_volume for s in self._steps])),
        }
