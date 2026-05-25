import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class AccountManager:
    """
    Manages betting accounts across different bookmakers.
    Implements account rotation, proxy mapping, and stake splitting
    to avoid limits and bans, prioritizing Betfair Exchange for high liquidity.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sandbox = os.getenv("BETTING_ENV", "production").lower() != "production"
        
        # Load credentials from .env
        self.betfair_app_key = os.getenv("BETFAIR_APP_KEY", "")
        self.betfair_cert = os.getenv("BETFAIR_CERT_PATH", "")
        self.betfair_key = os.getenv("BETFAIR_KEY_PATH", "")
        
        # Mock database of accounts. In production, this comes from the DB securely.
        self.accounts = {
            "betfair_main": {"type": "exchange", "balance": float(os.getenv("BF_START_BAL", "5000")), "status": "active", "commission": 0.02},
            "bet365_profile1": {"type": "soft", "balance": 500.0, "status": "active", "limit_status": "clean", "bets_today": 0, "last_bet_date": None},
            "bet365_profile2": {"type": "soft", "balance": 200.0, "status": "active", "limit_status": "warned", "bets_today": 0, "last_bet_date": None},
            "pinnacle_main": {"type": "sharp", "balance": 1500.0, "status": "active"}
        }

    def get_available_balance(self) -> float:
        """Returns total aggregate balance across all active accounts."""
        return sum(acc["balance"] for acc in self.accounts.values() if acc["status"] == "active")

    def route_stake(self, bookmaker: str, requested_stake: float) -> List[Dict[str, Any]]:
        """
        Routes the stake intelligently.
        If it's a soft book (e.g., bet365) and stake > safe_limit, it splits across profiles.
        It also enforces a strict 1-2 bets per day limit on soft books to avoid algorithmic flags.
        If it's an exchange or sharp book, it places it directly if balance allows.
        """
        routes = []
        remaining_stake = requested_stake
        today = datetime.now().date().isoformat()
        
        # 1. Soft Book Routing (Rotation)
        if bookmaker.lower() == "bet365":
            # Reset counters if it's a new day
            for acc in self.accounts.values():
                if acc["type"] == "soft" and acc.get("last_bet_date") != today:
                    acc["bets_today"] = 0
                    acc["last_bet_date"] = today

            soft_accounts = [
                (k, v) for k, v in self.accounts.items() 
                if v["type"] == "soft" and v["status"] == "active" and "bet365" in k.lower()
                and v["bets_today"] < 2  # STRICT LIMIT: Max 2 bets per day per soft profile
            ]
            
            # Sort by "clean" limit status first
            soft_accounts.sort(key=lambda x: 0 if x[1]["limit_status"] == "clean" else 1)
            
            for acc_id, acc_data in soft_accounts:
                if remaining_stake <= 0:
                    break
                    
                # Artificial safe limit for soft books to avoid detection
                safe_limit = 100.0 if acc_data["limit_status"] == "clean" else 20.0
                allocate = min(remaining_stake, safe_limit, acc_data["balance"])
                
                if allocate > 0:
                    # Rounding to avoid "weird" decimal stakes which trigger soft book algorithms
                    allocate = round(allocate) 
                    routes.append({"account_id": acc_id, "allocated_stake": allocate, "proxy": f"proxy_{acc_id}"})
                    remaining_stake -= allocate
                    
                    # Update daily bets counter
                    acc_data["bets_today"] += 1
                    
            # If we still have stake left, we might fall back to Betfair if odds are comparable
            if remaining_stake > 0:
                self.logger.warning(f"Could not route {remaining_stake} on soft books. Limits reached or accounts maxed out for today.")
                
        # 2. Exchange / Sharp Routing
        elif bookmaker.lower() in ["betfair", "pinnacle"]:
            target_acc = f"{bookmaker.lower()}_main"
            if target_acc in self.accounts and self.accounts[target_acc]["status"] == "active":
                balance = self.accounts[target_acc]["balance"]
                allocate = min(remaining_stake, balance)
                if allocate > 0:
                    routes.append({"account_id": target_acc, "allocated_stake": allocate, "proxy": "direct"})
                    remaining_stake -= allocate
                    
        return routes

    def apply_exchange_commission(self, raw_odd: float, commission_rate: Optional[float] = None) -> float:
        """
        Calculates the true odd on an Exchange after subtracting the commission on profits.
        Formula: True Odd = 1 + (Raw Odd - 1) * (1 - commission)

        Args:
            raw_odd: Raw decimal odds
            commission_rate: Commission rate (e.g., 0.05 for 5%). 
                If None, uses default 2% (Betfair default).
        """
        if commission_rate is None:
            commission_rate = 0.02
        profit_multiplier = raw_odd - 1.0
        net_profit_multiplier = profit_multiplier * (1.0 - commission_rate)
        return 1.0 + net_profit_multiplier
