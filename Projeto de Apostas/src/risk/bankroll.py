"""
Bankroll Management Module.
"""
from typing import Any, Dict, List

from .kelly import calculate_fractional_kelly


class BankrollManager:
    def __init__(self, initial_bankroll: float):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        self.bet_history: List[Dict[str, Any]] = []
        
    def calculate_stake(self, probability: float, odds: float) -> float:
        """
        Calculates stake based on Kelly fractional and limits.
        """
        kelly_frac = calculate_fractional_kelly(probability, odds, kelly_multiplier=0.25)
        
        stake = self.current_bankroll * kelly_frac
        
        # Absolute boundaries as per risk guidelines
        max_stake = self.current_bankroll * 0.02   # 2% max
        min_stake = self.current_bankroll * 0.001  # 0.1% min
        
        if stake < min_stake:
            return 0.0
            
        return min(stake, max_stake)
        
    def update_bankroll(self, stake: float, odds: float, result: str):
        if result == 'win':
            profit = stake * (odds - 1)
            self.current_bankroll += profit
        elif result == 'loss':
            self.current_bankroll -= stake
            
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
            
        self.bet_history.append({
            'stake': stake,
            'odds': odds,
            'result': result,
            'bankroll_after': self.current_bankroll
        })
