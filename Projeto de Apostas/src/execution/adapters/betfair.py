import json
import logging
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger("betfair_adapter")

def enforce_rate_limit(max_calls_per_sec: int = 5) -> Callable:
    """
    Decorator to prevent Betfair API rate-limit bans (e.g. Too Many Requests).
    """
    last_call = [0.0]
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_call[0]
            delay = (1.0 / max_calls_per_sec) - elapsed
            if delay > 0:
                time.sleep(delay)
            res = func(*args, **kwargs)
            last_call[0] = time.time()
            return res
        return wrapper
    return decorator


class BetfairAPIConnector:
    """
    Simulates a Betfair Exchange API client.
    Supports Back/Lay order placing, TLS session authentication, heartbeats, and rate-limiting.
    """
    def __init__(self, account_id: str, commission_rate: float = 0.05, sandbox: bool = False):
        self.account_id = account_id
        self.commission_rate = commission_rate
        self.sandbox = sandbox
        self.session_token = None
        self.last_heartbeat = None
        
        if self.sandbox:
            logger.info("Betfair API initialized in SANDBOX (Paper Trading) mode.")

    def authenticate_session(self, app_key: str, cert_path: str, key_path: str) -> bool:
        """
        Simulates Betfair SSL client certificate authentication.
        """
        if self.sandbox:
            self.session_token = f"SANDBOX-SESSION-{app_key[:5]}"
            self.last_heartbeat = time.time()
            logger.info(f"Sandbox session authenticated. Token: {self.session_token}")
            return True
            
        if not app_key or not cert_path or not key_path:
            logger.error("Authentication failed: app_key and cert paths must be provided.")
            return False
            
        # Simulate real certificate validation
        self.session_token = f"BF-SESSION-{app_key[:5]}-XYZ123"
        self.last_heartbeat = time.time()
        logger.info(f"Betfair session authenticated successfully. Token: {self.session_token}")
        return True

    def keep_alive_heartbeat(self) -> bool:
        """
        Sends a heartbeat packet to extend session token lifespan.
        Betfair session tokens expire every 20 minutes if not kept alive.
        """
        if not self.session_token:
            logger.warning("Heartbeat failed: No active session token.")
            return False
            
        self.last_heartbeat = time.time()
        logger.info("Heartbeat sent successfully. Session token extended.")
        return True

    @enforce_rate_limit(max_calls_per_sec=10)
    def get_market_depth(self, market_id: str) -> Dict[str, List[Dict[str, float]]]:
        """
        Returns simulated Betfair order book depth.
        """
        return {
            "back": [
                {"price": 1.95, "size": 200.0},
                {"price": 1.92, "size": 500.0},
                {"price": 1.88, "size": 1000.0}
            ],
            "lay": [
                {"price": 1.98, "size": 150.0},
                {"price": 2.02, "size": 400.0},
                {"price": 2.08, "size": 800.0}
            ]
        }

    @enforce_rate_limit(max_calls_per_sec=5)
    def place_back_order(self, market_id: str, odds: float, stake: float) -> Dict[str, Any]:
        """
        Places a BACK order on the exchange.
        """
        if not self.session_token:
            return self._log_execution(market_id, odds, stake, "REJECTED", 0.0, 0.0, "UNAUTHORIZED_NO_SESSION")
            
        if self.sandbox:
            # Paper trading always assumes perfect fill at requested odds for now
            return self._log_execution(market_id, odds, stake, "FULLY_FILLED", stake, odds, None)
            
        depth = self.get_market_depth(market_id)
        available_back = depth["back"]
        
        filled_stake = 0.0
        weighted_odds_sum = 0.0
        remaining_stake = stake
        
        for level in available_back:
            if remaining_stake <= 0:
                break
                
            if level["price"] >= odds:
                match_size = min(remaining_stake, level["size"])
                filled_stake += match_size
                weighted_odds_sum += match_size * level["price"]
                remaining_stake -= match_size
                
        if filled_stake == 0.0:
            return self._log_execution(market_id, odds, stake, "REJECTED", 0.0, 0.0, "NO_MATCHING_LIQUIDITY")
            
        avg_odds = weighted_odds_sum / filled_stake
        status = "FULLY_FILLED" if remaining_stake == 0 else "PARTIALLY_FILLED"
        
        return self._log_execution(market_id, odds, stake, status, filled_stake, avg_odds, None)

    def _log_execution(
        self, market_id: str, requested_odds: float, requested_stake: float, 
        status: str, filled_stake: float, average_odds: float, reason: str = None
    ) -> Dict[str, Any]:
        """
        Logs order execution in JSON format for easy ingestion by log aggregators.
        """
        payload = {
            "timestamp": time.time(),
            "account_id": self.account_id,
            "sandbox_mode": self.sandbox,
            "action": "PLACE_BACK_ORDER",
            "market_id": market_id,
            "requested_odds": requested_odds,
            "requested_stake": requested_stake,
            "status": status,
            "filled_stake": filled_stake,
            "average_odds": average_odds,
            "unfilled_stake": requested_stake - filled_stake,
            "reason": reason
        }
        
        # Write JSON formatted log
        logger.info(json.dumps(payload))
        return payload

    def calculate_net_profit(self, filled_stake: float, odds: float, won: bool) -> float:
        """
        Calculates Net PnL deducting Betfair commission fees.
        """
        if not won:
            return -filled_stake
            
        gross_profit = filled_stake * (odds - 1.0)
        commission = gross_profit * self.commission_rate
        return gross_profit - commission

    def calculate_true_edge(self, raw_odd: float, model_prob: float) -> float:
        """
        Calculates the actual expected edge on Betfair AFTER commission is deducted.
        """
        # True Odd = 1 + (Raw Odd - 1) * (1 - commission)
        profit_multiplier = raw_odd - 1.0
        net_profit_multiplier = profit_multiplier * (1.0 - self.commission_rate)
        true_odd = 1.0 + net_profit_multiplier
        
        # Edge = (True Odd * Model Prob) - 1
        return (true_odd * model_prob) - 1.0
