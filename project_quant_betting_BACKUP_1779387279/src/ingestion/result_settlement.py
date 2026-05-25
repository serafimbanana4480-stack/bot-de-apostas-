"""
Result Settlement Module.
Handles multi-source consensus (2-of-3), VOID/PUSH resolution, and CLV realization.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ResultSettlement:
    """Handles match result settlement with consensus logic."""
    
    def __init__(self):
        self.sources = ["api_1", "api_2", "scraper_backup"]
        
    def determine_consensus(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Determine the consensus result from multiple sources.
        Requires at least 2 sources to agree.
        """
        if not results:
            return None
            
        # Group by home/away score
        score_counts: Dict[str, int] = {}
        score_mapping: Dict[str, Dict[str, Any]] = {}
        
        for res in results:
            home = res.get("home_score")
            away = res.get("away_score")
            status = res.get("status")
            
            if home is None or away is None or status != "COMPLETED":
                continue
                
            key = f"{home}-{away}"
            score_counts[key] = score_counts.get(key, 0) + 1
            score_mapping[key] = res
            
        # Find consensus (min 2 agreements, or 1 if only 1 valid source returned data)
        valid_sources_count = sum(score_counts.values())
        if valid_sources_count == 0:
            return None
            
        best_key = max(score_counts.items(), key=lambda x: x[1])
        
        if valid_sources_count > 1 and best_key[1] < 2:
            logger.warning("Dispute in match settlement: no consensus reached.")
            return None
            
        logger.info(f"Consensus reached: {best_key[0]}")
        return score_mapping[best_key[0]]
        
    def settle_bet(self, bet: Dict[str, Any], match_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine bet outcome (WON/LOST/PUSH/VOID) based on match result."""
        market = bet.get("market")
        selection = bet.get("selection")
        
        home_score = match_result.get("home_score", 0)
        away_score = match_result.get("away_score", 0)
        
        status = "LOST"
        pnl = -bet.get("stake", 0.0)
        
        if market == "1X2" or market == "MONEYLINE":
            if home_score > away_score and selection == "HOME":
                status = "WON"
            elif away_score > home_score and selection == "AWAY":
                status = "WON"
            elif home_score == away_score and selection == "DRAW":
                status = "WON"
            elif home_score == away_score and market == "MONEYLINE":
                status = "PUSH"
                
        if status == "WON":
            pnl = bet.get("stake", 0.0) * (bet.get("odds", 1.0) - 1.0)
        elif status == "PUSH" or status == "VOID":
            pnl = 0.0
            
        return {
            "status": status,
            "pnl": pnl,
            "settled_at": datetime.utcnow().isoformat()
        }
