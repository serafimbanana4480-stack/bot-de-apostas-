import logging
from typing import Any, Dict, List

logger = logging.getLogger("result_settlement")

class ResultConsensusSettlement:
    """
    Validates and settles match outcomes by fetching results from multiple sources
    and enforcing consensus validation rules. Handles abandoned matches and overtimes.
    """
    def __init__(self, required_agreement_count: int = 2):
        self.required_agreement_count = required_agreement_count

    def resolve_outcome(self, event_id: str, source_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolidates results from sources.
        Payload format: {"source": "espn", "status": "FINISHED", "home_score": 102, "away_score": 98}
        """
        if len(source_payloads) < self.required_agreement_count:
            return {"status": "PENDING", "reason": "INSUFFICIENT_SOURCES", "event_id": event_id}

        # Check for void conditions (cancellations, postponements)
        void_votes = 0
        score_votes: Dict[tuple, int] = {}
        
        for payload in source_payloads:
            status = payload.get("status", "FINISHED").upper()
            if status in ["CANCELLED", "POSTPONED", "ABANDONED"]:
                void_votes += 1
            else:
                home = payload.get("home_score")
                away = payload.get("away_score")
                if home is not None and away is not None:
                    score_votes[(home, away)] = score_votes.get((home, away), 0) + 1

        # Check if void consensus is reached
        if void_votes >= self.required_agreement_count:
            logger.warning(f"Consensus reached: Void match for {event_id}")
            return {"status": "VOID", "event_id": event_id, "home_score": 0, "away_score": 0}

        # Find the score key with maximum consensus
        if not score_votes:
            return {"status": "ERROR", "reason": "NO_VALID_SCORES", "event_id": event_id}
            
        best_score, votes = max(score_votes.items(), key=lambda item: item[1])
        
        if votes >= self.required_agreement_count:
            home, away = best_score
            winner = "HOME" if home > away else "AWAY"
            logger.info(f"Consensus reached for {event_id}: Home {home} - Away {away} (Winner: {winner})")
            return {
                "status": "SETTLED",
                "event_id": event_id,
                "home_score": home,
                "away_score": away,
                "winner": winner
            }
            
        logger.error(f"Consensus failed for {event_id}. Score distribution: {score_votes}")
        return {"status": "DISCREPANCY", "reason": "NO_CONSENSUS_REACHED", "event_id": event_id}
