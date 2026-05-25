"""
Circuit Breakers Module.
Protects the bankroll from catastrophic drawdowns.
"""
import math
from typing import Any, Dict, List, Optional


class DailyLossCircuitBreaker:
    def __init__(self, max_daily_loss_pct: float = 5.0):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.daily_pnl = 0.0
        self.bankroll_start = 0.0
        
    def check(self) -> bool:
        if self.bankroll_start <= 0:
            return True
        loss_pct = (self.daily_pnl / self.bankroll_start) * 100
        return loss_pct > -self.max_daily_loss_pct

class DrawdownCircuitBreaker:
    def __init__(self, max_drawdown_pct: float = 20.0):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_bankroll = 0.0
        self.current_bankroll = 0.0
        
    def check(self) -> bool:
        if self.peak_bankroll <= 0:
            return True
        drawdown_pct = ((self.peak_bankroll - self.current_bankroll) / self.peak_bankroll) * 100
        return drawdown_pct < self.max_drawdown_pct

class StreakCircuitBreaker:
    def __init__(self, max_loss_streak: int = 5):
        self.max_loss_streak = max_loss_streak
        self.current_loss_streak = 0
        
    def record_bet(self, result: str):
        if result == 'loss':
            self.current_loss_streak += 1
        else:
            self.current_loss_streak = 0
            
    def check(self) -> bool:
        return self.current_loss_streak < self.max_loss_streak

class VolatilityCircuitBreaker:
    def __init__(self, max_volatility_threshold: float = 2.0):
        self.max_volatility_threshold = max_volatility_threshold
        self.pnl_history: List[float] = []
        
    def record_pnl(self, current_pnl: float):
        self.pnl_history.append(current_pnl)
        
    def check(self) -> bool:
        if len(self.pnl_history) < 20:
            return True
        recent_pnl = self.pnl_history[-20:]
        mean = sum(recent_pnl) / len(recent_pnl)
        variance = sum((x - mean) ** 2 for x in recent_pnl) / len(recent_pnl)
        std_dev = math.sqrt(variance)
        return std_dev <= self.max_volatility_threshold


class ModelDegradationCircuitBreaker:
    """
    Zeta-level circuit breaker: triggers when model predictions drift
    significantly from recent historical accuracy (e.g. Brier score degradation).
    """
    def __init__(self, max_brier_increase: float = 0.05, min_samples: int = 50):
        self.max_brier_increase = max_brier_increase
        self.min_samples = min_samples
        self.baseline_brier: Optional[float] = None
        self.recent_bets: List[Dict[str, Any]] = []

    def record_bet(self, predicted_prob: float, actual_outcome: int, won: bool):
        """actual_outcome should be 1 for win, 0 for loss."""
        self.recent_bets.append({
            "predicted_prob": predicted_prob,
            "actual_outcome": actual_outcome,
        })
        # Keep rolling window
        if len(self.recent_bets) > 500:
            self.recent_bets = self.recent_bets[-500:]

    def _compute_brier(self, bets: List[Dict[str, Any]]) -> float:
        if len(bets) < self.min_samples:
            return 0.0
        return sum((b["predicted_prob"] - b["actual_outcome"]) ** 2 for b in bets) / len(bets)

    def check(self) -> bool:
        if len(self.recent_bets) < self.min_samples:
            return True
        current_brier = self._compute_brier(self.recent_bets)
        if self.baseline_brier is None:
            self.baseline_brier = current_brier
            return True
        increase = current_brier - self.baseline_brier
        return increase <= self.max_brier_increase
