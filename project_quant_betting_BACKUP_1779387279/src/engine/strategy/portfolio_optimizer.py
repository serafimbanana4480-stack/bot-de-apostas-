"""
Portfolio Optimizer — Markowitz Mean-Variance for Correlated Bets.

Allocates capital across a slate of correlated betting opportunities using
mean-variance optimization with:
* Ledoit-Wolf covariance shrinkage (analytic oracle approximation factor).
* Per-bet and total exposure caps.
* Kelly upper-bound constraint.
* Optional CVXPY quadratic solver with gradient-projection fallback.

Reference (improved from):
    Projeto de Apostas › src/strategy_engine/portfolio_optimizer.py
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class BetCandidate(BaseModel):
    """Single bet opportunity to be included in the portfolio."""
    bet_id: str
    event_id: str
    market: str = ""
    ev: float = Field(description="Expected Value as a fraction (e.g. 0.05 = 5%).")
    probability: float = Field(ge=0.0, le=1.0)
    odds: float = Field(gt=1.0)
    kelly_fraction: float = Field(ge=0.0, description="Raw Kelly fraction for this bet.")
    bankroll: float = Field(gt=0, description="Current bankroll to allocate from.")


class PortfolioAllocation(BaseModel):
    """Result of portfolio optimisation for a single bet."""
    bet_id: str
    event_id: str
    market: str
    ev: float
    portfolio_weight: float = Field(ge=0.0, description="Fraction of bankroll [0-1].")
    allocated_stake: float = Field(ge=0.0, description="Absolute stake in base currency.")
    kelly_fraction: float
    was_capped: bool = False
    cap_reason: str = ""


class PortfolioResult(BaseModel):
    """Full portfolio optimisation output."""
    allocations: list[PortfolioAllocation]
    total_exposure: float = Field(ge=0.0, description="Sum of weights (fraction of bankroll).")
    solver_used: str = "gradient_projection"
    converged: bool = True


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class PortfolioConfig:
    """Tunable parameters for the optimizer."""
    risk_aversion_lambda: float = 2.0         # λ in quadratic penalty
    max_single_bet_exposure: float = 0.05     # 5% max per bet
    max_total_exposure: float = 0.30          # 30% total bankroll at risk
    kelly_cap_multiplier: float = 1.0         # weight ≤ kelly * this

    # Ledoit-Wolf shrinkage
    shrinkage_intensity: float | None = None  # None → auto (Oracle Approx.)
    shrinkage_floor: float = 0.05             # minimum shrinkage

    # Solver
    solver_iterations: int = 500
    solver_learning_rate: float = 0.02
    solver_tolerance: float = 1e-8
    use_cvxpy: bool = False                   # try CVXPY if available


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PortfolioOptimizer:
    """Markowitz mean-variance optimizer for bet portfolios.

    Improvements over reference:
    * Ledoit-Wolf with automatic Oracle Approximating Shrinkage.
    * Kelly upper-bound per bet (prevents over-allocation).
    * Total-exposure constraint (sum of weights ≤ cap).
    * Optional CVXPY QP solver with gradient-projection fallback.
    * Pydantic domain models for type-safe I/O.

    Args:
        config: Optimisation parameters.
    """

    def __init__(self, config: PortfolioConfig | None = None) -> None:
        self.config = config or PortfolioConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        candidates: Sequence[BetCandidate],
        covariance_matrix: np.ndarray,
    ) -> PortfolioResult:
        """Compute optimal capital allocation across *candidates*.

        Args:
            candidates: List of ``BetCandidate`` objects.
            covariance_matrix: ``(n, n)`` sample covariance of bet returns.

        Returns:
            ``PortfolioResult`` with per-bet allocations.

        Raises:
            ValueError: If dimensions mismatch or inputs are invalid.
        """
        n = len(candidates)
        if n == 0:
            return PortfolioResult(allocations=[], total_exposure=0.0)

        cov = np.asarray(covariance_matrix, dtype=np.float64)
        if cov.shape != (n, n):
            raise ValueError(f"Covariance shape {cov.shape} does not match {n} candidates.")

        mu = np.array([c.ev for c in candidates], dtype=np.float64)
        kelly_caps = np.array(
            [min(c.kelly_fraction * self.config.kelly_cap_multiplier, self.config.max_single_bet_exposure)
             for c in candidates],
            dtype=np.float64,
        )

        # Shrink covariance
        shrunk_cov = self._shrink_covariance(cov)

        # Solve
        weights, solver, converged = self._solve(mu, shrunk_cov, kelly_caps)

        # Build results
        allocations: list[PortfolioAllocation] = []
        for i, c in enumerate(candidates):
            w = float(weights[i])
            capped = False
            cap_reason = ""

            if w >= self.config.max_single_bet_exposure - 1e-9:
                capped = True
                cap_reason = "max_single_bet_exposure"
            elif w >= kelly_caps[i] - 1e-9 and kelly_caps[i] < self.config.max_single_bet_exposure:
                capped = True
                cap_reason = "kelly_cap"

            allocations.append(PortfolioAllocation(
                bet_id=c.bet_id,
                event_id=c.event_id,
                market=c.market,
                ev=c.ev,
                portfolio_weight=w,
                allocated_stake=w * c.bankroll,
                kelly_fraction=c.kelly_fraction,
                was_capped=capped,
                cap_reason=cap_reason,
            ))

        return PortfolioResult(
            allocations=allocations,
            total_exposure=float(weights.sum()),
            solver_used=solver,
            converged=converged,
        )

    # ------------------------------------------------------------------
    # Covariance shrinkage
    # ------------------------------------------------------------------

    def _shrink_covariance(self, sample_cov: np.ndarray) -> np.ndarray:
        """Apply Ledoit-Wolf-style shrinkage towards diagonal target.

        ``Σ_shrunk = (1 - δ) · S + δ · diag(S)``

        If ``shrinkage_intensity`` is None, uses the Oracle Approximating
        Shrinkage estimator (OAS) heuristic.
        """
        cfg = self.config
        n = sample_cov.shape[0]

        if cfg.shrinkage_intensity is not None:
            delta = np.clip(cfg.shrinkage_intensity, cfg.shrinkage_floor, 1.0)
        else:
            # OAS simplified heuristic: δ* ≈ (1 - 2/p) · tr(S²) + tr²(S)
            #                               / (n + 1 - 2/p)(tr(S²) + tr²(S))
            trace_s = np.trace(sample_cov)
            trace_s2 = np.trace(sample_cov @ sample_cov)
            rho_num = (1.0 - 2.0 / max(n, 1)) * trace_s2 + trace_s ** 2
            rho_den = (n + 1.0 - 2.0 / max(n, 1)) * (trace_s2 - trace_s ** 2 / max(n, 1))
            delta = float(np.clip(rho_num / max(rho_den, 1e-12), cfg.shrinkage_floor, 1.0))

        target = np.diag(np.diag(sample_cov))
        shrunk = (1.0 - delta) * sample_cov + delta * target

        logger.debug("Covariance shrinkage applied with δ=%.4f", delta)
        return shrunk

    # ------------------------------------------------------------------
    # Solvers
    # ------------------------------------------------------------------

    def _solve(
        self,
        mu: np.ndarray,
        cov: np.ndarray,
        kelly_caps: np.ndarray,
    ) -> tuple[np.ndarray, str, bool]:
        """Dispatch to CVXPY or gradient projection."""
        if self.config.use_cvxpy:
            try:
                return self._solve_cvxpy(mu, cov, kelly_caps)
            except Exception as exc:  # noqa: BLE001
                logger.warning("CVXPY solver failed (%s), falling back to gradient projection.", exc)

        return self._solve_gradient_projection(mu, cov, kelly_caps)

    def _solve_cvxpy(
        self, mu: np.ndarray, cov: np.ndarray, kelly_caps: np.ndarray,
    ) -> tuple[np.ndarray, str, bool]:
        """Quadratic programme via CVXPY."""
        import cvxpy as cp  # type: ignore[import-untyped]

        n = len(mu)
        w = cp.Variable(n)
        lam = self.config.risk_aversion_lambda

        objective = cp.Maximize(mu @ w - (lam / 2) * cp.quad_form(w, cov))
        constraints = [
            w >= 0,
            w <= kelly_caps,
            cp.sum(w) <= self.config.max_total_exposure,
        ]

        prob = cp.Problem(objective, constraints)
        prob.solve(solver=cp.OSQP, warm_start=True)

        if prob.status in ("optimal", "optimal_inaccurate"):
            return np.array(w.value).flatten(), "cvxpy_osqp", True
        raise RuntimeError(f"CVXPY status: {prob.status}")

    def _solve_gradient_projection(
        self, mu: np.ndarray, cov: np.ndarray, kelly_caps: np.ndarray,
    ) -> tuple[np.ndarray, str, bool]:
        """Projected gradient ascent (no external deps)."""
        cfg = self.config
        n = len(mu)
        w = np.zeros(n, dtype=np.float64)
        lr = cfg.solver_learning_rate
        prev_obj = -np.inf

        upper = np.minimum(kelly_caps, cfg.max_single_bet_exposure)

        for iteration in range(cfg.solver_iterations):
            grad = mu - cfg.risk_aversion_lambda * (cov @ w)
            w_new = w + lr * grad

            # Project: box constraints [0, upper_i]
            w_new = np.clip(w_new, 0.0, upper)

            # Project: total exposure ≤ max_total_exposure (proportional scaling)
            total = w_new.sum()
            if total > cfg.max_total_exposure:
                w_new *= cfg.max_total_exposure / total

            # Check convergence
            obj = float(mu @ w_new - (cfg.risk_aversion_lambda / 2) * w_new @ cov @ w_new)
            if abs(obj - prev_obj) < cfg.solver_tolerance:
                return w_new, "gradient_projection", True
            prev_obj = obj
            w = w_new

        logger.debug("Gradient projection did not converge in %d iterations.", cfg.solver_iterations)
        return w, "gradient_projection", False
