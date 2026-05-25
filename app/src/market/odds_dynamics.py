from typing import Any, Dict, List

import numpy as np


class OddsDynamicsEngine:
    """
    Predicts pre-match odds movement trends (shortening vs drifting) 
    and forecasts the Closing Line Value (CLV).
    """
    def __init__(self):
        pass

    def predict_odds_trend(
        self, 
        current_odds: float, 
        odds_history: List[float], 
        hours_to_kickoff: float, 
        volume_ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        Predicts if odds will shorten (go down), drift (go up), or remain stable.
        Uses historical momentum and time-decay factors.
        """
        if len(odds_history) < 2:
            return {"trend": "STABLE", "momentum": 0.0}

        # Calculate momentum: negative means price is dropping (shortening)
        momentum = (odds_history[-1] - odds_history[0]) / odds_history[0]
        
        # Closer to kickoff, line adjustments are typically faster and driven by heavy volumes
        decay_factor = 1.0 / max(0.5, hours_to_kickoff)
        weighted_drift = momentum * decay_factor * volume_ratio
        
        if weighted_drift < -0.01:
            trend = "SHORTEN"
        elif weighted_drift > 0.01:
            trend = "DRIFT"
        else:
            trend = "STABLE"
            
        return {
            "trend": trend,
            "momentum": float(momentum),
            "weighted_drift": float(weighted_drift)
        }

    def predict_closing_odds(self, current_odds: float, hours_to_kickoff: float, sharp_sentiment: float = 0.0) -> float:
        """
        Predicts the expected Closing Line Odds.
        sharp_sentiment: negative value implies sharp pressure is pushing the odd down.
        """
        # Odds drift towards the efficient closing line based on sharp flow
        expected_drift = sharp_sentiment * (1.0 / max(1.0, hours_to_kickoff))
        predicted_close = current_odds * (1.0 + expected_drift)
        return float(max(1.01, predicted_close))

    def calculate_expected_clv_edge(self, current_odds: float, predicted_closing_odds: float) -> float:
        """
        Calculates expected edge against the predicted closing line (CLV).
        Edge = (current_odds / predicted_closing_odds) - 1.0
        """
        if predicted_closing_odds <= 1.0:
            return 0.0
        return float((current_odds / predicted_closing_odds) - 1.0)


class SharpMoneyDetector:
    """
    Identifies high-conviction institutional flow (Sharp Money).
    Tracks reverse line movement and steam moves.
    """
    def __init__(self):
        pass

    def detect_steam_move(self, time_series_odds: List[float], volume_changes: List[float]) -> bool:
        """
        Steam Move: Rapid price drop across multiple books simultaneously driven by high volume.
        """
        if len(time_series_odds) < 3 or len(volume_changes) < 2:
            return False
            
        # Check if odds dropped quickly in the last 2 periods
        drop = (time_series_odds[-1] - time_series_odds[-3]) / time_series_odds[-3]
        vol_spike = volume_changes[-1] > 2.5 * np.mean(volume_changes[:-1])
        
        return bool(drop < -0.02 and vol_spike)

    def detect_reverse_line_movement(
        self, 
        public_bet_percentage: float, 
        odds_movement: float
    ) -> bool:
        """
        Reverse Line Movement: Odds move against public betting consensus.
        Indicates heavy sharp backing on the less popular side.
        public_bet_percentage: percentage of tickets on team A (0.0 to 1.0)
        odds_movement: positive means team A odds drifted up (became less favored),
                       negative means team A odds shortened (became more favored).
        """
        # If 70% of tickets are on Team A, but Team A's odds drift UP (odds_movement > 0.015),
        # it implies that large institutional (sharp) stakes are backing Team B.
        return bool(public_bet_percentage > 0.65 and odds_movement > 0.015)
