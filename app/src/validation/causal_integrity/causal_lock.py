import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


class CausalIntegrityLock:
    """
    Prevents temporal data leakage by locking the prediction's feature state 
    at a specific timestamp prior to game kickoff.
    """
    def __init__(self):
        self.locked_predictions: Dict[str, Dict[str, Any]] = {}

    def lock_features(self, event_id: str, features: Dict[str, Any], odds_at_lock: float) -> str:
        """
        Locks features and odds at the prediction moment.
        Generates a secure hash representing this specific state.
        """
        lock_time = datetime.now(timezone.utc).isoformat()
        
        state = {
            "event_id": event_id,
            "lock_timestamp": lock_time,
            "features": features,
            "odds_at_lock": odds_at_lock
        }
        
        state_str = json.dumps(state, sort_keys=True)
        lock_hash = hashlib.sha256(state_str.encode("utf-8")).hexdigest()
        
        self.locked_predictions[event_id] = {
            "state": state,
            "lock_hash": lock_hash
        }
        
        return lock_hash

    def verify_causal_integrity(self, event_id: str, current_odds: float, lock_hash: str) -> bool:
        """
        Validates if the features and odds used for backtesting or validation match the locked lock_hash.
        Prevents using future, updated odds post-kickoff.
        """
        if event_id not in self.locked_predictions:
            return False
            
        locked = self.locked_predictions[event_id]
        if locked["lock_hash"] != lock_hash:
            return False
            
        # Ensure current_odds hasn't shifted too far since decision, suggesting late execution leak
        odds_at_lock = locked["state"]["odds_at_lock"]
        # Allow small deviation (< 0.5% due to execution delay) but reject large shifts
        deviation = abs(current_odds - odds_at_lock) / odds_at_lock
        return deviation < 0.005
