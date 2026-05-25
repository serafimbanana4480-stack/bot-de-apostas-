"""
Ledger Accounting Module.
Handles P&L tracking, multi-currency conversion, and ROI calculations.
"""
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

class Ledger:
    """Core accounting engine for the betting system."""
    
    def __init__(self, initial_balance: float = 1000.0, base_currency: str = "EUR"):
        self.initial_balance = initial_balance
        self.base_currency = base_currency
        self.current_balance = initial_balance
        self.bets: List[Dict[str, Any]] = []
        
    def record_bet(self, bet: Dict[str, Any]) -> None:
        """Record a placed bet."""
        # Validate required fields
        for field in ["id", "stake", "odds", "status"]:
            if field not in bet:
                raise ValueError(f"Missing required field: {field}")
                
        self.bets.append(bet)
        
        # Deduct stake from available balance if pending/placed
        if bet["status"] in ["PENDING", "PLACED"]:
            self.current_balance -= bet["stake"]
            
    def settle_bet(self, bet_id: str, status: str, pnl: float, closing_odds: float = None) -> bool:
        """Update a bet's status and apply P&L to the balance."""
        for bet in self.bets:
            if bet["id"] == bet_id:
                bet["status"] = "SETTLED"
                bet["settlement_status"] = status
                bet["pnl"] = pnl
                
                if closing_odds:
                    bet["closing_odds"] = closing_odds
                    bet["clv_pct"] = (bet["odds"] / closing_odds) - 1.0
                    
                # Restore the originally deducted stake, then add the full PnL 
                # (which includes the stake if WON, or is just 0 if PUSH, or negative stake if LOST)
                self.current_balance += bet["stake"]
                self.current_balance += pnl
                return True
                
        return False
        
    def get_summary(self) -> Dict[str, float]:
        """Calculate overall ROI and P&L metrics."""
        settled_bets = [b for b in self.bets if b.get("status") == "SETTLED"]
        
        if not settled_bets:
            return {"roi": 0.0, "total_pnl": 0.0, "win_rate": 0.0, "total_staked": 0.0}
            
        total_pnl = sum(b.get("pnl", 0) for b in settled_bets)
        total_staked = sum(b.get("stake", 0) for b in settled_bets)
        
        wins = sum(1 for b in settled_bets if b.get("settlement_status") == "WON")
        
        roi = (total_pnl / total_staked) if total_staked > 0 else 0.0
        win_rate = (wins / len(settled_bets)) if settled_bets else 0.0
        
        # Calculate mean CLV if available
        clv_values = [b.get("clv_pct") for b in settled_bets if b.get("clv_pct") is not None]
        mean_clv = sum(clv_values) / len(clv_values) if clv_values else 0.0
        
        return {
            "total_pnl": float(total_pnl),
            "roi_pct": float(roi * 100),
            "win_rate_pct": float(win_rate * 100),
            "total_staked": float(total_staked),
            "mean_clv_pct": float(mean_clv * 100)
        }
