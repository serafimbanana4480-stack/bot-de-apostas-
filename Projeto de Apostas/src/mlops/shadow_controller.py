import logging
from typing import Any, Dict, List

logger = logging.getLogger("shadow_controller")

class LiveShadowController:
    """
    Orchestrates real-time model shadow deployments. 
    Intercepts live feeds to evaluate candidate models without executing financial wagers.
    """
    def __init__(self, champion_id: str, challenger_id: str):
        self.champion_id = champion_id
        self.challenger_id = challenger_id
        self.shadow_logs: List[Dict[str, Any]] = []

    def process_live_opportunity(
        self, 
        event_id: str, 
        current_odds: float, 
        champ_prediction_func: lambda: float, 
        chall_prediction_func: lambda: float
    ) -> Dict[str, Any]:
        """
        Calculates predictions for both models and logs virtual decisions.
        """
        # Get probabilities
        p_champ = champ_prediction_func()
        p_chall = chall_prediction_func()
        
        # Calculate EV
        ev_champ = (p_champ * current_odds) - 1.0
        ev_chall = (p_chall * current_odds) - 1.0
        
        # Decision decisions: EV > 2% is a BET
        decision_champ = "BET" if ev_champ > 0.02 else "SKIP"
        decision_chall = "BET" if ev_chall > 0.02 else "SKIP"
        
        log_entry = {
            "event_id": event_id,
            "current_odds": current_odds,
            "champion": {
                "id": self.champion_id,
                "prob": p_champ,
                "ev": ev_champ,
                "decision": decision_champ
            },
            "challenger": {
                "id": self.challenger_id,
                "prob": p_chall,
                "ev": ev_chall,
                "decision": decision_chall
            }
        }
        
        self.shadow_logs.append(log_entry)
        logger.info(f"Shadow opportunity resolved for {event_id}. Champ: {decision_champ}, Chall: {decision_chall}")
        return log_entry

    def get_shadow_performance_metrics(self) -> Dict[str, Any]:
        """
        Summarizes decision alignment and discrepancy count between champion and challenger.
        """
        total = len(self.shadow_logs)
        if total == 0:
            return {"total_tracked": 0, "discrepancy_rate": 0.0}
            
        discrepancies = 0
        for log in self.shadow_logs:
            if log["champion"]["decision"] != log["challenger"]["decision"]:
                discrepancies += 1
                
        return {
            "total_tracked": total,
            "discrepancies": discrepancies,
            "discrepancy_rate": float(discrepancies / total)
        }
