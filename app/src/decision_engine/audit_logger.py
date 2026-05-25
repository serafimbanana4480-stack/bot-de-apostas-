import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("decision_audit")


class DecisionAuditLogger:
    """
    Maintains a persistent, regulatory-grade JSON audit trail of all decision steps:
    1. Decision inputs (features, timestamps).
    2. Model outputs (predicted probability, EV, calibration indicators).
    3. Operational risk constraints (circuit breaker state, CVaR threshold flags, final Kelly sizing).
    4. Counterfactual explanations (why a bet was rejected and what would change that).
    5. Slippage estimates and execution quality metrics.
    """
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def record_decision(
        self, 
        event_id: str, 
        features: Dict[str, Any], 
        predicted_prob: float, 
        market_odds: float,
        kelly_fraction: float,
        risk_evaluation: Dict[str, Any],
        decision_status: str,
        reason: str,
        counterfactual: Optional[Dict[str, Any]] = None,
        slippage: Optional[Dict[str, Any]] = None,
        bandit_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates and stores a detailed log entry.

        Args:
            event_id: Unique event identifier
            features: Feature summary dict
            predicted_prob: Model predicted probability
            market_odds: Available market odds
            kelly_fraction: Kelly criterion fraction
            risk_evaluation: Risk assessment results
            decision_status: BET_NOW, WAIT, NO_BET
            reason: Human-readable decision reason
            counterfactual: Optional counterfactual explanation for rejected bets
            slippage: Optional slippage estimate details
            bandit_info: Optional bandit model selection details
        """
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "inputs": {
                "market_odds": market_odds,
                "features_summary": {k: float(v) for k, v in features.items() if isinstance(v, (int, float, np.integer, np.floating))}
            },
            "model_outputs": {
                "predicted_prob": float(predicted_prob),
                "expected_value": float((predicted_prob * market_odds) - 1.0)
            },
            "risk_metrics": {
                "kelly_fraction": float(kelly_fraction),
                "risk_evaluation": risk_evaluation
            },
            "outcome": {
                "decision": decision_status,
                "reason": reason
            },
        }

        # Add counterfactual explanation if available
        if counterfactual is not None:
            log_entry["counterfactual"] = counterfactual

        # Add slippage estimate if available
        if slippage is not None:
            log_entry["slippage"] = slippage

        # Add bandit selection info if available
        if bandit_info is not None:
            log_entry["bandit"] = bandit_info

        self.logs.append(log_entry)
        logger.info(f"Audit trail recorded for {event_id}. Status: {decision_status}. Reason: {reason}")
        return log_entry

    def export_audit_trail_json(self) -> str:
        """Serializes the audit logs history."""
        return json.dumps(self.logs, indent=2)

    def get_rejected_with_counterfactuals(self) -> List[Dict[str, Any]]:
        """Return all rejected bets that have counterfactual explanations."""
        return [
            log for log in self.logs
            if log.get("outcome", {}).get("decision") not in ("BET_NOW", "BET")
            and log.get("counterfactual") is not None
        ]

    def get_slippage_stats(self) -> Dict[str, Any]:
        """Compute aggregate slippage statistics across all logged decisions."""
        slippages = [
            log["slippage"]["slippage_bps"]
            for log in self.logs
            if log.get("slippage") and "slippage_bps" in log.get("slippage", {})
        ]
        if not slippages:
            return {"count": 0}
        return {
            "count": len(slippages),
            "avg_bps": float(np.mean(slippages)),
            "max_bps": float(np.max(slippages)),
            "median_bps": float(np.median(slippages)),
        }
