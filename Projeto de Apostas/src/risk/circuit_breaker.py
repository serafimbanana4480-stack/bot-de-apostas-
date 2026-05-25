import logging
from typing import Any, Dict, List

logger = logging.getLogger("circuit_breaker")

class CircuitBreaker:
    """
    Prevents execution when operational safety constraints are breached:
    1. Drawdown threshold: freezes system if 24h rolling loss is > 10% of bankroll.
    2. Balance buffer check: validates balance against order size with 10% headroom.
    """
    def __init__(self, initial_bankroll: float = 1000.0, max_drawdown_limit: float = 0.10, alert_callback=None):
        self.initial_bankroll = initial_bankroll
        self.max_drawdown_limit = max_drawdown_limit
        self.current_bankroll = initial_bankroll
        self.pnl_history: List[float] = [] # list of pnl results
        self.is_paused = False
        self._alert_callback = alert_callback

    def record_pnl_result(self, pnl: float):
        """Records bet P&L and updates current bankroll state."""
        self.pnl_history.append(pnl)
        self.current_bankroll += pnl
        
        # Check drawdown from initial bankroll
        drawdown = (self.initial_bankroll - self.current_bankroll) / self.initial_bankroll
        if drawdown > self.max_drawdown_limit:
            self.is_paused = True
            logger.critical(f"Circuit Breaker Triggered: Drawdown ({drawdown:.2%}) exceeded limit ({self.max_drawdown_limit:.2%})")
            if self._alert_callback:
                try:
                    self._alert_callback(
                        level="CRITICAL",
                        title="Circuit Breaker Triggered",
                        message=f"Drawdown {drawdown:.2%} exceeded limit {self.max_drawdown_limit:.2%}. All betting paused.",
                        data={"drawdown_pct": round(drawdown * 100, 2), "bankroll": self.current_bankroll},
                    )
                except Exception as e:
                    logger.error("Alert callback failed: %s", e)

    def validate_wager(self, bet_stake: float) -> Dict[str, Any]:
        """
        Validates if wager fits safety margin buffers.
        """
        if self.is_paused:
            return {"action": "ABORT", "reason": "CIRCUIT_BREAKER_ACTIVE"}
            
        required_buffer = bet_stake * 1.10
        if self.current_bankroll < required_buffer:
            logger.warning(f"Insufficient funds: Wager stake {bet_stake} requires buffer size {required_buffer:.2f}")
            return {"action": "ABORT", "reason": "INSUFFICIENT_BALANCE_BUFFER"}
            
        return {"action": "PROCEED", "available_bankroll": self.current_bankroll}
