import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("override")

class HumanOverrideLog:
    """
    Registers and evaluates manual overrides (SKIPS, stake modifications) 
    triggered by Telegram operator input.
    """
    def __init__(self):
        self.override_records: List[Dict[str, Any]] = []

    def record_override(
        self, 
        event_id: str, 
        original_stake: float, 
        override_stake: float, 
        action: str, # "SKIP", "RESIZE"
        reason: str
    ) -> Dict[str, Any]:
        """
        Records the manual change in the override ledger.
        """
        record = {
            "event_id": event_id,
            "original_stake": original_stake,
            "override_stake": override_stake,
            "action": action,
            "reason": reason,
            "settled": False,
            "original_pnl": 0.0,
            "actual_pnl": 0.0
        }
        self.override_records.append(record)
        logger.warning(f"HUMAN OVERRIDE: Event {event_id} was modified via action: {action}. Reason: {reason}")
        return record

    def settle_override(self, event_id: str, won: bool, odds: float) -> Optional[Dict[str, Any]]:
        """
        Settles the override record and calculates the hypothetical difference (PnL diff).
        """
        for record in self.override_records:
            if record["event_id"] == event_id and not record["settled"]:
                record["settled"] = True
                
                # If won, PnL is stake * (odds - 1), else -stake
                orig_stake = record["original_stake"]
                act_stake = record["override_stake"]
                
                if won:
                    record["original_pnl"] = orig_stake * (odds - 1.0)
                    record["actual_pnl"] = act_stake * (odds - 1.0)
                else:
                    record["original_pnl"] = -orig_stake
                    record["actual_pnl"] = -act_stake
                    
                record["pnl_difference"] = record["actual_pnl"] - record["original_pnl"]
                return record
        return None

    def evaluate_override_performance(self) -> Dict[str, float]:
        """
        Measures if manual overrides are adding or detracting value from the model.
        """
        settled_records = [r for r in self.override_records if r["settled"]]
        if not settled_records:
            return {"net_pnl_impact": 0.0, "total_overrides": 0.0}
            
        net_impact = sum(r["actual_pnl"] - r["original_pnl"] for r in settled_records)
        return {
            "net_pnl_impact": float(net_impact),
            "total_overrides": float(len(settled_records)),
            "skips_count": float(sum(1 for r in settled_records if r["action"] == "SKIP"))
        }
