"""
Reconciliation engine — verifies account balance consistency after order execution.

Detects discrepancies between expected and actual balance changes,
which could indicate: partial fills, rejected orders, API errors,
or unauthorized activity.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("reconciliation")


class ReconciliationEngine:
    """
    Verifies account balance before and after each order placement.
    Flags anomalies and triggers alerts when discrepancies are detected.
    """

    def __init__(
        self,
        log_path: str = "logs/reconciliation.jsonl",
        tolerance_pct: float = 0.01,
        alert_callback: Optional[Any] = None,
    ):
        """
        Args:
            log_path: Path to reconciliation audit log
            tolerance_pct: Acceptable balance discrepancy as % of stake (default 1%)
            alert_callback: Callable for alerting on anomalies (e.g., Telegram alerter)
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.tolerance_pct = tolerance_pct
        self.alert_callback = alert_callback

        self._pending_checks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()  # Thread-safety for pending checks

    def record_pre_balance(
        self,
        order_id: str,
        balance_before: float,
        stake: float,
        odds: float,
        bookmaker: str,
        market_id: str = "",
    ) -> None:
        """
        Record account balance before placing an order.

        Call this BEFORE sending the order to the bookmaker API.
        """
        with self._lock:
            self._pending_checks[order_id] = {
                "order_id": order_id,
                "balance_before": balance_before,
                "stake": stake,
                "odds": odds,
                "bookmaker": bookmaker,
                "market_id": market_id,
                "timestamp_before": time.time(),
            }
        logger.info(
            "Pre-balance recorded: order=%s balance=%.2f stake=%.2f",
            order_id, balance_before, stake,
        )

    def verify_post_balance(
        self,
        order_id: str,
        balance_after: float,
        filled_stake: float,
        fill_status: str,
        bet_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify account balance after order execution.

        Call this AFTER receiving the order response from the bookmaker API.

        Returns:
            Reconciliation result with anomaly detection.
        """
        with self._lock:
            pending = self._pending_checks.pop(order_id, None)
        if not pending:
            logger.warning("No pre-balance record for order %s", order_id)
            return {"order_id": order_id, "status": "NO_PRE_RECORD", "anomaly": True}

        balance_before = pending["balance_before"]
        stake = pending["stake"]
        bookmaker = pending["bookmaker"]

        # Expected balance change
        # For unmatched/pending bets: balance should decrease by filled_stake
        # For matched bets that won: balance should increase by filled_stake * (odds - 1)
        # For matched bets that lost: balance already decreased by filled_stake
        # Immediately after placing: balance should decrease by filled_stake (exposure)
        expected_balance_after = balance_before - filled_stake

        actual_change = balance_after - balance_before
        expected_change = -filled_stake
        discrepancy = abs(actual_change - expected_change)
        if stake > 0:
            discrepancy_pct = discrepancy / stake
        else:
            logger.warning("Zero stake in reconciliation for order=%s", order_id)
            discrepancy_pct = 0.0

        is_anomaly = discrepancy_pct > self.tolerance_pct

        result = {
            "order_id": order_id,
            "bet_id": bet_id,
            "bookmaker": bookmaker,
            "market_id": pending.get("market_id", ""),
            "balance_before": balance_before,
            "balance_after": balance_after,
            "expected_balance_after": expected_balance_after,
            "actual_change": actual_change,
            "expected_change": expected_change,
            "discrepancy": discrepancy,
            "discrepancy_pct": round(discrepancy_pct, 6),
            "filled_stake": filled_stake,
            "fill_status": fill_status,
            "anomaly_detected": is_anomaly,
            "timestamp_before": pending["timestamp_before"],
            "timestamp_after": time.time(),
        }

        # Log result
        self._write_log(result)

        if is_anomaly:
            logger.warning(
                "RECONCILIATION ANOMALY: order=%s expected_change=%.2f actual_change=%.2f "
                "discrepancy=%.2f (%.4f%%)",
                order_id, expected_change, actual_change, discrepancy, discrepancy_pct * 100,
            )
            if self.alert_callback:
                try:
                    self.alert_callback(
                        level="CRITICAL",
                        title="Reconciliation Anomaly",
                        message=(
                            f"Order {order_id} on {bookmaker}: "
                            f"Expected balance change {expected_change:.2f}, "
                            f"actual {actual_change:.2f}. "
                            f"Discrepancy: {discrepancy:.2f} ({discrepancy_pct*100:.2f}%)"
                        ),
                        data=result,
                    )
                except Exception as e:
                    logger.error("Alert callback failed: %s", e)
        else:
            logger.info(
                "Reconciliation OK: order=%s change=%.2f (expected %.2f)",
                order_id, actual_change, expected_change,
            )

        return result

    def verify_settlement(
        self,
        order_id: str,
        balance_after_settlement: float,
        balance_before_settlement: float,
        expected_pnl: float,
        bet_won: bool,
    ) -> Dict[str, Any]:
        """
        Verify balance after bet settlement (result known).

        Args:
            order_id: Original order ID
            balance_after_settlement: Balance after settlement
            balance_before_settlement: Balance before settlement
            expected_pnl: Expected PnL based on odds and commission
            bet_won: Whether the bet won
        """
        actual_pnl = balance_after_settlement - balance_before_settlement
        discrepancy = abs(actual_pnl - expected_pnl)
        is_anomaly = discrepancy > abs(expected_pnl) * self.tolerance_pct

        result = {
            "order_id": order_id,
            "settlement_type": "BET_SETTLEMENT",
            "balance_before": balance_before_settlement,
            "balance_after": balance_after_settlement,
            "expected_pnl": expected_pnl,
            "actual_pnl": actual_pnl,
            "discrepancy": discrepancy,
            "bet_won": bet_won,
            "anomaly_detected": is_anomaly,
            "timestamp": time.time(),
        }

        self._write_log(result)

        if is_anomaly:
            logger.warning(
                "SETTLEMENT ANOMALY: order=%s expected_pnl=%.2f actual_pnl=%.2f discrepancy=%.2f",
                order_id, expected_pnl, actual_pnl, discrepancy,
            )
            if self.alert_callback:
                try:
                    self.alert_callback(
                        level="WARNING",
                        title="Settlement Anomaly",
                        message=(
                            f"Order {order_id}: Expected PnL {expected_pnl:.2f}, "
                            f"actual {actual_pnl:.2f}. Discrepancy: {discrepancy:.2f}"
                        ),
                        data=result,
                    )
                except Exception as e:
                    logger.error("Alert callback failed: %s", e)

        return result

    def get_pending_count(self) -> int:
        """Number of orders awaiting reconciliation."""
        with self._lock:
            return len(self._pending_checks)

    def get_pending_orders(self) -> List[str]:
        """List of order IDs awaiting reconciliation."""
        with self._lock:
            return list(self._pending_checks.keys())

    def _write_log(self, entry: Dict[str, Any]) -> None:
        """Append reconciliation entry to audit log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
