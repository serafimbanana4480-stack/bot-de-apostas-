"""
Rigorous balance validation before each bet placement.

Ensures that:
1. The account has sufficient real balance for the bet
2. The simulated balance matches the real balance (within tolerance)
3. The available balance after pending bets is still sufficient
4. No stale balance data is used (max age check)
5. Currency mismatches are caught

This module is called by the execution engine before any order is sent
to the bookmaker, providing a last line of defense against:
- Over-betting due to stale balance
- Phantom balance from failed reconciliation
- Currency conversion errors
- Simulated vs real balance drift
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("balance_validator")


class ValidationVerdict(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    verdict: ValidationVerdict
    message: str
    real_balance: Optional[float] = None
    simulated_balance: Optional[float] = None
    drift_pct: Optional[float] = None
    available_after_bet: Optional[float] = None
    balance_age_seconds: Optional[float] = None


@dataclass
class BalanceSnapshot:
    """A point-in-time balance reading from a bookmaker."""
    total_balance: float
    available_balance: float  # After pending bets
    currency: str = "EUR"
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"  # "real_api" or "simulated"

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    @property
    def is_stale(self) -> bool:
        return self.age_seconds > 60  # 1 minute max age


class BalanceValidator:
    """
    Validates balance before each bet placement.

    Checks:
    1. Sufficient available balance for the stake
    2. Balance is not stale (fetched recently)
    3. Real vs simulated balance drift within tolerance
    4. Available balance after this bet remains positive
    5. Currency consistency
    """

    def __init__(
        self,
        max_drift_pct: float = 5.0,
        max_balance_age_seconds: float = 60.0,
        min_reserve_pct: float = 5.0,
        warn_drift_pct: float = 2.0,
    ):
        """
        Args:
            max_drift_pct: Maximum allowed drift between real and simulated balance (%)
            max_balance_age_seconds: Maximum age of balance data before it's stale
            min_reserve_pct: Minimum % of total balance to keep as reserve after bet
            warn_drift_pct: Drift % that triggers a warning (but still passes)
        """
        self.max_drift_pct = max_drift_pct
        self.max_balance_age_seconds = max_balance_age_seconds
        self.min_reserve_pct = min_reserve_pct
        self.warn_drift_pct = warn_drift_pct

        self._last_real_snapshot: Optional[BalanceSnapshot] = None
        self._last_simulated_snapshot: Optional[BalanceSnapshot] = None

    def update_real_balance(self, snapshot: BalanceSnapshot) -> None:
        """Update the last known real balance from the API."""
        snapshot.source = "real_api"
        self._last_real_snapshot = snapshot
        logger.info(
            "Real balance updated: %.2f %s (available: %.2f)",
            snapshot.total_balance, snapshot.currency, snapshot.available_balance,
        )

    def update_simulated_balance(self, snapshot: BalanceSnapshot) -> None:
        """Update the last known simulated balance from the accounting system."""
        snapshot.source = "simulated"
        self._last_simulated_snapshot = snapshot

    def validate(
        self,
        stake: float,
        currency: str = "EUR",
        force: bool = False,
    ) -> ValidationResult:
        """
        Validate that a bet of the given stake can be placed.

        Args:
            stake: The amount to bet
            currency: Expected currency of the bet
            force: If True, skip validation (for emergency overrides)

        Returns:
            ValidationResult with verdict and details
        """
        if force:
            return ValidationResult(
                verdict=ValidationVerdict.WARN,
                message="Validation bypassed with force flag",
            )

        # --- Check 1: We have a real balance snapshot ---
        if self._last_real_snapshot is None:
            return ValidationResult(
                verdict=ValidationVerdict.FAIL,
                message="No real balance data available — fetch balance first",
            )

        real = self._last_real_snapshot

        # --- Check 2: Balance is not stale ---
        if real.age_seconds > self.max_balance_age_seconds:
            return ValidationResult(
                verdict=ValidationVerdict.FAIL,
                message=f"Real balance is stale ({real.age_seconds:.0f}s old, max {self.max_balance_age_seconds}s)",
                balance_age_seconds=real.age_seconds,
            )

        # --- Check 3: Currency consistency ---
        if real.currency != currency:
            return ValidationResult(
                verdict=ValidationVerdict.FAIL,
                message=f"Currency mismatch: balance is {real.currency}, bet is {currency}",
                real_balance=real.available_balance,
            )

        # --- Check 4: Sufficient available balance ---
        if real.available_balance < stake:
            return ValidationResult(
                verdict=ValidationVerdict.FAIL,
                message=f"Insufficient balance: available {real.available_balance:.2f}, need {stake:.2f}",
                real_balance=real.available_balance,
            )

        # --- Check 5: Reserve after bet ---
        reserve = real.total_balance * (self.min_reserve_pct / 100.0)
        available_after = real.available_balance - stake
        if available_after < reserve:
            return ValidationResult(
                verdict=ValidationVerdict.FAIL,
                message=f"Would breach reserve: {available_after:.2f} remaining < {reserve:.2f} reserve ({self.min_reserve_pct}%)",
                available_after_bet=available_after,
            )

        # --- Check 6: Real vs simulated drift ---
        drift_pct = None
        if self._last_simulated_snapshot is not None:
            sim = self._last_simulated_snapshot
            if sim.total_balance > 0:
                drift_pct = abs(real.total_balance - sim.total_balance) / sim.total_balance * 100

                if drift_pct > self.max_drift_pct:
                    return ValidationResult(
                        verdict=ValidationVerdict.FAIL,
                        message=f"Balance drift too large: {drift_pct:.1f}% (max {self.max_drift_pct}%)",
                        real_balance=real.total_balance,
                        simulated_balance=sim.total_balance,
                        drift_pct=drift_pct,
                    )

                if drift_pct > self.warn_drift_pct:
                    logger.warning(
                        "Balance drift warning: %.1f%% (real=%.2f, sim=%.2f)",
                        drift_pct, real.total_balance, sim.total_balance,
                    )

        # All checks passed
        return ValidationResult(
            verdict=ValidationVerdict.PASS,
            message="Balance validation passed",
            real_balance=real.total_balance,
            simulated_balance=self._last_simulated_snapshot.total_balance if self._last_simulated_snapshot else None,
            drift_pct=drift_pct,
            available_after_bet=available_after,
            balance_age_seconds=real.age_seconds,
        )

    def get_status(self) -> dict:
        """Get current validator status for monitoring."""
        real = self._last_real_snapshot
        sim = self._last_simulated_snapshot
        return {
            "real_balance": {"total": real.total_balance, "available": real.available_balance, "currency": real.currency, "age_s": round(real.age_seconds, 1)} if real else None,
            "simulated_balance": {"total": sim.total_balance, "currency": sim.currency, "age_s": round(sim.age_seconds, 1)} if sim else None,
            "drift_pct": round(abs(real.total_balance - sim.total_balance) / sim.total_balance * 100, 2) if real and sim and sim.total_balance > 0 else None,
        }
