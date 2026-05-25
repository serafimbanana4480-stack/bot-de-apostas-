"""
Risk Manager Module.
Orchestrates Kelly criterion, exposure limits, and circuit breakers.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RiskManager:
    """Central risk manager orchestrating all risk limits."""
    
    def __init__(self, bankroll_manager, circuit_breakers: List[Any]):
        self.bankroll = bankroll_manager
        self.circuit_breakers = circuit_breakers
        self.max_exposure_per_match = 0.05 # 5% max on a single match
        
    def calculate_allowed_stake(self, match_id: str, probability: float, odds: float) -> float:
        """
        Calculate the allowed stake for a bet, considering all risk limits.
        """
        # 1. Check all circuit breakers
        for breaker in self.circuit_breakers:
            if not breaker.check():
                logger.warning(f"Circuit breaker {type(breaker).__name__} triggered. Blocking bet.")
                return 0.0
                
        # 2. Base Kelly Calculation (from BankrollManager)
        base_stake = self.bankroll.calculate_stake(probability, odds)
        
        if base_stake <= 0:
            return 0.0
            
        # 3. Check specific exposure limits
        # E.g., we cannot exceed max_exposure_per_match
        max_allowed_stake = self.bankroll.current_bankroll * self.max_exposure_per_match
        
        final_stake = min(base_stake, max_allowed_stake)
        
        logger.info(f"Risk Manager approved stake: {final_stake}")
        return final_stake
