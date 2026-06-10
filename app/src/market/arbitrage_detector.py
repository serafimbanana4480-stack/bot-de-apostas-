"""
Arbitrage Detector — Identifies risk-free opportunities across bookmakers.

Uses The Odds API free tier (500 req/month) to compare odds from 3+ bookmakers.
An arbitrage exists when the sum of implied probabilities < 1.0.

Example:
    Bookmaker A: Home 2.10
    Bookmaker B: Draw 3.50
    Bookmaker C: Away 4.20

    Implied probs: 1/2.10 + 1/3.50 + 1/4.20 = 0.952 < 1.0 → arbitrage!
    Guaranteed ROI: (1 - 0.952) / 0.952 ≈ 5.0%
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity."""
    match_id: str
    home_team: str
    away_team: str
    league: str
    date: str
    # Best odds per outcome
    best_home_odd: float
    best_draw_odd: float
    best_away_odd: float
    # Bookmakers offering best odds
    home_bookmaker: str
    draw_bookmaker: str
    away_bookmaker: str
    # Metrics
    implied_prob_sum: float
    guaranteed_roi_pct: float
    # Stake allocation for 100 unit profit
    stakes: Dict[str, float] = field(default_factory=dict)


class ArbitrageDetector:
    """
    Detect arbitrage opportunities across multiple bookmakers.
    """

    def __init__(self, min_guaranteed_roi: float = 0.005):
        """
        Args:
            min_guaranteed_roi: Minimum guaranteed ROI to report (default 0.5%)
        """
        self.min_guaranteed_roi = min_guaranteed_roi

    def find_arbitrages(
        self,
        odds_data: List[Dict[str, Any]],
    ) -> List[ArbitrageOpportunity]:
        """
        Find arbitrages from raw odds data.

        Args:
            odds_data: List of dicts, each representing a match with odds from multiple bookmakers.
                Format per dict:
                {
                    "match_id": "...",
                    "home_team": "...",
                    "away_team": "...",
                    "league": "...",
                    "date": "...",
                    "bookmakers": [
                        {
                            "name": "Pinnacle",
                            "odds": {"home": 2.10, "draw": 3.40, "away": 3.80}
                        },
                        ...
                    ]
                }

        Returns:
            List of ArbitrageOpportunity
        """
        opportunities = []

        for match in odds_data:
            bms = match.get("bookmakers", [])
            if len(bms) < 2:
                continue

            best = {
                "home": (0.0, ""),
                "draw": (0.0, ""),
                "away": (0.0, ""),
            }

            for bm in bms:
                name = bm.get("name", "unknown")
                odds = bm.get("odds", {})
                for outcome in ["home", "draw", "away"]:
                    odd = odds.get(outcome, 0.0)
                    if odd > best[outcome][0]:
                        best[outcome] = (odd, name)

            if any(v[0] <= 1.0 for v in best.values()):
                continue

            implied_sum = sum(1.0 / v[0] for v in best.values())
            if implied_sum >= 1.0:
                continue

            guaranteed_roi = (1.0 - implied_sum) / implied_sum
            if guaranteed_roi < self.min_guaranteed_roi:
                continue

            # Calculate stakes for equal profit
            stakes = self._calculate_stakes(best, implied_sum)

            opp = ArbitrageOpportunity(
                match_id=match.get("match_id", ""),
                home_team=match.get("home_team", ""),
                away_team=match.get("away_team", ""),
                league=match.get("league", ""),
                date=match.get("date", ""),
                best_home_odd=best["home"][0],
                best_draw_odd=best["draw"][0],
                best_away_odd=best["away"][0],
                home_bookmaker=best["home"][1],
                draw_bookmaker=best["draw"][1],
                away_bookmaker=best["away"][1],
                implied_prob_sum=implied_sum,
                guaranteed_roi_pct=guaranteed_roi,
                stakes=stakes,
            )
            opportunities.append(opp)

        return opportunities

    def find_arbitrages_from_odds_api(
        self,
        api_response: List[Dict[str, Any]],
    ) -> List[ArbitrageOpportunity]:
        """
        Parse The Odds API response format.

        Args:
            api_response: Raw JSON from The Odds API /sports/{sport}/odds endpoint
        """
        odds_data = []
        for event in api_response:
            bookmakers = []
            for bm in event.get("bookmakers", []):
                h2h = next(
                    (m for m in bm.get("markets", []) if m.get("key") == "h2h"),
                    None,
                )
                if not h2h:
                    continue
                outcomes = {o["name"]: o["price"] for o in h2h.get("outcomes", [])}
                # Map names to home/draw/away
                home_team = event.get("home_team", "")
                away_team = event.get("away_team", "")
                odds = {}
                for name, price in outcomes.items():
                    if name == home_team:
                        odds["home"] = price
                    elif name == away_team:
                        odds["away"] = price
                    elif name.lower() in ("draw", "tie"):
                        odds["draw"] = price

                if len(odds) >= 2:
                    bookmakers.append({"name": bm.get("title", ""), "odds": odds})

            odds_data.append({
                "match_id": event.get("id", ""),
                "home_team": home_team,
                "away_team": away_team,
                "league": event.get("sport_title", ""),
                "date": event.get("commence_time", ""),
                "bookmakers": bookmakers,
            })

        return self.find_arbitrages(odds_data)

    def _calculate_stakes(
        self,
        best: Dict[str, Tuple[float, str]],
        implied_sum: float,
    ) -> Dict[str, float]:
        """
        Calculate stake proportions for risk-free profit.
        Stakes are percentages of total bankroll allocated.
        """
        stakes = {}
        for outcome in ["home", "draw", "away"]:
            odd = best[outcome][0]
            # Stake proportional to 1 / (odd * implied_sum)
            stakes[outcome] = (1.0 / (odd * implied_sum))
        return stakes

    def to_dataframe(self, opportunities: List[ArbitrageOpportunity]) -> pd.DataFrame:
        """Convert opportunities to DataFrame."""
        if not opportunities:
            return pd.DataFrame()
        records = []
        for opp in opportunities:
            records.append({
                "match_id": opp.match_id,
                "home_team": opp.home_team,
                "away_team": opp.away_team,
                "league": opp.league,
                "date": opp.date,
                "best_home_odd": opp.best_home_odd,
                "best_draw_odd": opp.best_draw_odd,
                "best_away_odd": opp.best_away_odd,
                "home_bookmaker": opp.home_bookmaker,
                "draw_bookmaker": opp.draw_bookmaker,
                "away_bookmaker": opp.away_bookmaker,
                "implied_prob_sum": opp.implied_prob_sum,
                "guaranteed_roi_pct": opp.guaranteed_roi_pct,
            })
        return pd.DataFrame(records)


def demo_arbitrage():
    """Demonstrate arbitrage detection with synthetic data."""
    sample_data = [
        {
            "match_id": "match_1",
            "home_team": "Team A",
            "away_team": "Team B",
            "league": "Premier League",
            "date": "2024-01-01",
            "bookmakers": [
                {"name": "Pinnacle", "odds": {"home": 2.10, "draw": 3.40, "away": 3.80}},
                {"name": "Bet365", "odds": {"home": 2.05, "draw": 3.50, "away": 4.20}},
                {"name": "Betfair", "odds": {"home": 2.00, "draw": 3.60, "away": 4.00}},
            ],
        },
        {
            "match_id": "match_2",
            "home_team": "Team C",
            "away_team": "Team D",
            "league": "La Liga",
            "date": "2024-01-02",
            "bookmakers": [
                {"name": "Pinnacle", "odds": {"home": 1.90, "draw": 3.50, "away": 4.50}},
                {"name": "Bet365", "odds": {"home": 1.85, "draw": 3.60, "away": 4.40}},
            ],
        },
    ]

    detector = ArbitrageDetector(min_guaranteed_roi=0.005)
    opps = detector.find_arbitrages(sample_data)
    print(f"Found {len(opps)} arbitrage opportunities")
    for opp in opps:
        print(f"  {opp.home_team} vs {opp.away_team}: ROI={opp.guaranteed_roi_pct:.2%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_arbitrage()
