import logging
from typing import Any, Dict, Tuple


class CLVTracker:
    """
    Closing Line Value (CLV) Tracker.
    This module evaluates the true Expected Value (EV) of historical bets by comparing
    the taken odds against the Pinnacle closing line (considered the ground truth).
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def remove_vig(odds_home: float, odds_draw: float, odds_away: float) -> Tuple[float, float, float]:
        """
        Removes the bookmaker's margin (vig) using proportional normalization.
        In production, more advanced methods (e.g. Shin's method) can be used.
        """
        raw_prob_home = 1.0 / odds_home
        raw_prob_draw = 1.0 / odds_draw
        raw_prob_away = 1.0 / odds_away
        
        implied_total = raw_prob_home + raw_prob_draw + raw_prob_away
        
        # Vig-free probabilities
        p_home = raw_prob_home / implied_total
        p_draw = raw_prob_draw / implied_total
        p_away = raw_prob_away / implied_total
        
        return p_home, p_draw, p_away

    @staticmethod
    def remove_vig_2way(odds_home: float, odds_away: float) -> Tuple[float, float]:
        """
        Removes vig for 2-way markets (e.g., UFC, Asian Handicap, Tennis).
        """
        raw_prob_home = 1.0 / odds_home
        raw_prob_away = 1.0 / odds_away
        
        implied_total = raw_prob_home + raw_prob_away
        
        return raw_prob_home / implied_total, raw_prob_away / implied_total

    def calculate_clv(
        self, 
        bet_odd: float, 
        bet_side: str, 
        closing_odds: Dict[str, float], 
        market_type: str = "3-way"
    ) -> Dict[str, Any]:
        """
        Calculates the Closing Line Value.
        
        :param bet_odd: The odd the bet was placed at.
        :param bet_side: "home", "draw", or "away".
        :param closing_odds: Dictionary with Pinnacle closing odds e.g. {"home": 2.10, "draw": 3.40, "away": 3.50}
        :param market_type: "2-way" or "3-way"
        :return: Dict containing CLV, Vig-Free Probability and Expected Value
        """
        if market_type == "3-way":
            p_home, p_draw, p_away = self.remove_vig(
                closing_odds["home"], closing_odds["draw"], closing_odds["away"]
            )
            prob_map = {"home": p_home, "draw": p_draw, "away": p_away}
        else:
            p_home, p_away = self.remove_vig_2way(closing_odds["home"], closing_odds["away"])
            prob_map = {"home": p_home, "away": p_away}
            
        if bet_side not in prob_map:
            raise ValueError(f"Invalid bet_side '{bet_side}' for market '{market_type}'")

        true_prob = prob_map[bet_side]
        true_fair_odd = 1.0 / true_prob
        
        # Calculate EV based on Pinnacle's true probability
        expected_value = (bet_odd * true_prob) - 1.0
        
        # CLV as percentage beat vs closing line
        clv_percentage = (bet_odd / true_fair_odd) - 1.0
        
        return {
            "true_prob": float(true_prob),
            "true_fair_odd": float(true_fair_odd),
            "expected_value": float(expected_value),
            "clv_percentage": float(clv_percentage),
            "is_sharp": expected_value > 0.0
        }

    def evaluate_portfolio(self, bet_history: list[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluates a portfolio of bets to determine if the model is generating real edge.
        Requires bet history to include bet_odd, bet_side, and Pinnacle closing odds.
        """
        total_ev = 0.0
        positive_clv_count = 0
        total_bets = len(bet_history)
        
        if total_bets == 0:
            return {}
            
        for bet in bet_history:
            market_type = bet.get("market_type", "3-way")
            clv_res = self.calculate_clv(
                bet_odd=bet["bet_odd"],
                bet_side=bet["bet_side"],
                closing_odds=bet["closing_odds"],
                market_type=market_type
            )
            total_ev += clv_res["expected_value"]
            if clv_res["clv_percentage"] > 0:
                positive_clv_count += 1
                
        avg_ev = total_ev / total_bets
        beat_closing_line_rate = positive_clv_count / total_bets
        
        self.logger.info(f"Portfolio Avg EV vs Pinnacle: {avg_ev*100:.2f}%")
        self.logger.info(f"Beat Closing Line Rate: {beat_closing_line_rate*100:.1f}%")
        
        return {
            "total_bets": total_bets,
            "avg_ev": avg_ev,
            "beat_closing_line_rate": beat_closing_line_rate
        }
