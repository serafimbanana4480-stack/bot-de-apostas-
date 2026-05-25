from typing import Any, Dict, List

import numpy as np


class CanaryEvaluator:
    """
    Simulates a challenger model's decisions on historical champion execution logs
    to block deployments of degraded candidates.
    """
    def __init__(self, max_divergence_pct: float = 30.0, max_simulated_loss_pct: float = 10.0):
        self.max_divergence_pct = max_divergence_pct
        self.max_simulated_loss_pct = max_simulated_loss_pct

    def evaluate_canary(
        self, 
        champion_decisions: List[Dict[str, Any]], 
        challenger_preds: np.ndarray,
        historical_odds: np.ndarray,
        historical_outcomes: np.ndarray
    ) -> Dict[str, Any]:
        """
        Runs mock simulation of challenger on past events.
        Compares BET/SKIP rate and PnL.
        """
        n_events = len(champion_decisions)
        if n_events == 0 or len(challenger_preds) != n_events:
            return {"deploy_approved": False, "reason": "Insufficient or mismatched validation samples"}

        champ_bets_count = sum(1 for d in champion_decisions if d.get("executed", False))
        
        # Calculate challenger decisions (BET if predicted prob > 1 / odds)
        challenger_bets_count = 0
        challenger_pnl = 0.0
        initial_bankroll = 1000.0
        current_bankroll = initial_bankroll
        
        for i in range(n_events):
            pred = challenger_preds[i]
            odds = historical_odds[i]
            outcome = historical_outcomes[i] # 1 for win, 0 for loss
            
            implied = 1.0 / odds
            edge = pred - implied
            
            if edge > 0.04: # Bet trigger threshold
                challenger_bets_count += 1
                stake = current_bankroll * 0.02 # 2% flat stake size
                
                if outcome == 1:
                    win_amt = stake * (odds - 1.0)
                    challenger_pnl += win_amt
                    current_bankroll += win_amt
                else:
                    challenger_pnl -= stake
                    current_bankroll -= stake
                    
        # Check divergence in bet rate
        divergence = abs(champ_bets_count - challenger_bets_count) / max(1, champ_bets_count) * 100.0
        
        # Check drawdown loss percentage
        loss_pct = (abs(challenger_pnl) / initial_bankroll * 100.0) if challenger_pnl < 0 else 0.0
        
        approved = True
        reasons = []
        
        if divergence > self.max_divergence_pct:
            approved = False
            reasons.append(f"Divergence in bet counts ({divergence:.1f}%) exceeds limit {self.max_divergence_pct}%")
            
        if loss_pct > self.max_simulated_loss_pct:
            approved = False
            reasons.append(f"Simulated drawdown ({loss_pct:.1f}%) exceeds safety threshold {self.max_simulated_loss_pct}%")
            
        return {
            "deploy_approved": approved,
            "reasons": reasons,
            "divergence_pct": divergence,
            "simulated_pnl": challenger_pnl,
            "simulated_bets_count": challenger_bets_count
        }
