from typing import Any, Dict, List

import numpy as np


class BettingSimulatorV2:
    """
    Hedge-fund grade betting backtest simulation framework.
    Injects realistic execution elements: latency slippage, bookmaker rejection, limit cuts,
    exchange commissions, and bankroll path evolution.
    """
    def __init__(self, initial_bankroll: float = 10000.0, commission_rate: float = 0.05):
        self.bankroll = initial_bankroll
        self.commission_rate = commission_rate
        self.history: List[Dict[str, Any]] = []

    def simulate_bet(
        self,
        event_id: str,
        predicted_prob: float,
        model_odds: float,
        actual_outcome_won: bool,
        slippage_deviation: float = 0.01,
        rejection_probability: float = 0.02,
        max_stake_cap: float = 500.0
    ) -> Dict[str, Any]:
        """
        Runs a full-stack execution simulation of a single bet.
        """
        # 1. Rejection Check (e.g. limit hit, account restriction, timeout)
        if np.random.rand() < rejection_probability:
            return {"event_id": event_id, "status": "REJECTED", "net_profit": 0.0, "final_bankroll": self.bankroll}
            
        # 2. Stake sizing (simple Kelly / unit sizing proxy)
        edge = (predicted_prob * model_odds) - 1.0
        if edge <= 0:
            return {"event_id": event_id, "status": "NO_BET", "net_profit": 0.0, "final_bankroll": self.bankroll}
            
        # Kelly: stake = edge / (odds - 1)
        kelly_fraction = edge / (model_odds - 1.0)
        raw_stake = self.bankroll * kelly_fraction * 0.10 # fractional Kelly (10%)
        
        # Apply bookmaker max limits cap
        stake = min(raw_stake, max_stake_cap)
        stake = max(10.0, stake) # min stake boundary
        
        # 3. Slippage injection (odds drift)
        # We assume execution latency causes negative slippage
        executed_odds = model_odds * (1.0 - np.abs(np.random.normal(0, slippage_deviation)))
        executed_odds = max(1.01, executed_odds)
        
        # 4. Result settlement
        if actual_outcome_won:
            gross = stake * (executed_odds - 1.0)
            commission = gross * self.commission_rate
            net_profit = gross - commission
        else:
            net_profit = -stake
            
        self.bankroll += net_profit
        
        record = {
            "event_id": event_id,
            "status": "EXECUTED",
            "stake": float(stake),
            "model_odds": float(model_odds),
            "executed_odds": float(executed_odds),
            "net_profit": float(net_profit),
            "final_bankroll": float(self.bankroll)
        }
        self.history.append(record)
        return record
