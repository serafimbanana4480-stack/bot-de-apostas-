"""
Decision Engine Module.
Orchestrates the bet decision process (BET_NOW, WAIT, NO_BET).
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Decision(BaseModel):
    match_id: str
    model_version: str
    market: str
    selection: str
    decision_type: str  # 'BET_NOW', 'WAIT', 'NO_BET'
    probability: float
    edge_pct: float
    recommended_stake_pct: float
    timestamp: datetime = datetime.utcnow()
    reason: str = ""

class DecisionEngine:
    """Core engine that makes betting decisions."""
    
    def __init__(self, risk_manager, timing_engine, odds_dynamics, dynamic_ev):
        self.risk_manager = risk_manager
        self.timing_engine = timing_engine
        self.odds_dynamics = odds_dynamics
        self.dynamic_ev = dynamic_ev
        
    def evaluate_opportunity(
        self, 
        match_id: str,
        market: str,
        selection: str,
        model_prob: float, 
        current_odds: float,
        time_to_kickoff_mins: float,
        model_version: str = "v1"
    ) -> Decision:
        """Evaluate a prediction and decide whether to bet."""
        
        # 1. Base edge calculation
        implied_prob = 1.0 / current_odds if current_odds > 0 else 0
        edge_pct = (model_prob - implied_prob) * 100.0
        
        if edge_pct <= 0:
            return Decision(
                match_id=match_id, model_version=model_version, market=market,
                selection=selection, decision_type="NO_BET", probability=model_prob,
                edge_pct=edge_pct, recommended_stake_pct=0.0, reason="Negative edge"
            )
            
        # 2. Timing and EV decay
        # For simplicity in this implementation, we query timing engine directly
        timing_decision = self.timing_engine.evaluate(
            edge_pct=edge_pct, 
            time_to_kickoff_mins=time_to_kickoff_mins
        ) if hasattr(self.timing_engine, 'evaluate') else "BET_NOW"
        
        if timing_decision == "WAIT":
            return Decision(
                match_id=match_id, model_version=model_version, market=market,
                selection=selection, decision_type="WAIT", probability=model_prob,
                edge_pct=edge_pct, recommended_stake_pct=0.0, reason="Waiting for better timing"
            )
            
        # 3. Risk Management & Sizing
        # Determine stake via Kelly and constraints
        stake_pct = self.risk_manager.calculate_allowed_stake(
            match_id=match_id,
            probability=model_prob,
            odds=current_odds
        )
        
        if stake_pct <= 0:
            return Decision(
                match_id=match_id, model_version=model_version, market=market,
                selection=selection, decision_type="NO_BET", probability=model_prob,
                edge_pct=edge_pct, recommended_stake_pct=0.0, reason="Blocked by risk limits"
            )
            
        return Decision(
            match_id=match_id, model_version=model_version, market=market,
            selection=selection, decision_type="BET_NOW", probability=model_prob,
            edge_pct=edge_pct, recommended_stake_pct=stake_pct, reason="Approved"
        )
