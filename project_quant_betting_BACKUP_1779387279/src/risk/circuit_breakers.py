"""
Circuit Breakers Module.
Protects the bankroll from catastrophic drawdowns.
"""
from typing import List
import math

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
