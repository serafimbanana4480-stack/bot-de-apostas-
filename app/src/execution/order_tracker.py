import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("execution")

class OrderTracker:
    """
    Tracks and logs bet execution details with strict structured audit trails.
    Includes slippage calculation and bet rejection handling.
    """
    def __init__(self, audit_log_path: str = "models/execution_audit.jsonl"):
        self.audit_log_path = audit_log_path
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

    def log_decision(self, decision_log: Dict[str, Any]) -> None:
        """
        Appends a structured JSON audit log entry for the betting decision.
        """
        required_keys = {
            "event_id", "timestamp", "model_version", "input_features_hash",
            "predicted_prob", "edge", "kelly_stake", "final_stake", 
            "odds_available", "odds_used", "executed", "result_settled",
            "human_override"
        }
        # Fill missing keys with defaults
        log_entry = {k: decision_log.get(k, None) for k in required_keys}
        if not log_entry["timestamp"]:
            log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
            
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Execution decision logged for event {log_entry['event_id']}")

    def calculate_slippage(self, odds_predicted: float, odds_executed: float) -> float:
        """
        Calculates slippage between predicted/available odds and actual executed odds.
        Negative slippage means worse execution price.
        """
        if odds_predicted <= 0:
            return 0.0
        return odds_executed - odds_predicted

    def handle_bet_rejection(
        self, 
        original_stake: float, 
        max_allowed_stake: Optional[float], 
        odds_available: float,
        min_acceptable_odds: float = 1.05
    ) -> Dict[str, Any]:
        """
        Decides whether to split, downsize, or abort a bet if the bookmaker rejects or limits the stake.
        """
        if odds_available < min_acceptable_odds:
            return {"action": "ABORT", "stake": 0.0, "reason": f"Odds {odds_available} below minimum {min_acceptable_odds}"}

        if max_allowed_stake is None or max_allowed_stake <= 0:
            return {"action": "ABORT", "stake": 0.0, "reason": "Bet rejected by bookmaker"}

        if max_allowed_stake >= original_stake:
            return {"action": "EXECUTE", "stake": original_stake, "reason": "Stake accepted fully"}

        # Partial acceptance: if allowed stake is at least 30% of original, accept the limit, else abort
        if max_allowed_stake >= (original_stake * 0.30):
            return {"action": "EXECUTE_REDUCED", "stake": max_allowed_stake, "reason": f"Original stake {original_stake} reduced to max allowed {max_allowed_stake}"}
        else:
            return {"action": "ABORT", "stake": 0.0, "reason": f"Allowed stake {max_allowed_stake} too low (<30% of original {original_stake})"}
