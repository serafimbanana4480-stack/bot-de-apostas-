from typing import Any, Dict


class DecisionTracer:
    """
    Traces and explains model decisions by identifying the contribution of each feature
    relative to a standard reference baseline.
    """
    def __init__(self, baseline_features: Dict[str, float] = None):
        # Default typical baselines for NBA features
        self.baselines = baseline_features or {
            "elo_diff": 0.0,
            "rest_diff": 0.0,
            "win_rate_5_diff": 0.0,
            "market_overround": 0.04
        }

    def trace_decision(self, features: Dict[str, float], predicted_prob: float) -> Dict[str, Any]:
        """
        Calculates positive and negative feature contributions based on deviation from baselines.
        """
        contributions = []
        
        # 1. Elo difference check
        elo_val = features.get("elo_diff", 0.0)
        if elo_val > self.baselines["elo_diff"]:
            contributions.append({
                "feature": "elo_diff",
                "value": elo_val,
                "impact": "positive",
                "reason": f"Elo difference ({elo_val:+.1f}) favors home team"
            })
        elif elo_val < self.baselines["elo_diff"]:
            contributions.append({
                "feature": "elo_diff",
                "value": elo_val,
                "impact": "negative",
                "reason": f"Elo difference ({elo_val:+.1f}) favors away team"
            })
            
        # 2. Rest difference check
        rest_val = features.get("rest_diff", 0.0)
        if rest_val > self.baselines["rest_diff"]:
            contributions.append({
                "feature": "rest_diff",
                "value": rest_val,
                "impact": "positive",
                "reason": f"Home team has rest advantage (+{rest_val} days)"
            })
        elif rest_val < self.baselines["rest_diff"]:
            contributions.append({
                "feature": "rest_diff",
                "value": rest_val,
                "impact": "negative",
                "reason": f"Home team has fatigue/rest disadvantage ({rest_val} days)"
            })

        # 3. Form difference check
        form_val = features.get("win_rate_5_diff", 0.0)
        if form_val > self.baselines["win_rate_5_diff"]:
            contributions.append({
                "feature": "win_rate_5_diff",
                "value": form_val,
                "impact": "positive",
                "reason": f"Home team has better recent form (+{form_val*100:.1f}%)"
            })
        elif form_val < self.baselines["win_rate_5_diff"]:
            contributions.append({
                "feature": "win_rate_5_diff",
                "value": form_val,
                "impact": "negative",
                "reason": f"Away team has better recent form ({form_val*100:.1f}%)"
            })

        return {
            "predicted_probability": predicted_prob,
            "contributions": contributions,
            "verdict": "STRONG_HOME" if predicted_prob > 0.60 else ("STRONG_AWAY" if predicted_prob < 0.40 else "NEUTRAL")
        }
