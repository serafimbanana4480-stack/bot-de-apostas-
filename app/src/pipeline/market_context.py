"""Build market context from odds history or open/close lines."""
from __future__ import annotations

from typing import Any, Dict, List

from src.ingestion.odds_ingestor import OddsIngestor


def build_odds_history_from_lines(
    opening_odd: float,
    current_odd: float,
    closing_odd: float,
    bet_side: str = "home",
) -> List[Dict[str, Any]]:
    """
    Synthetic 3-point history for backtest when Parquet snapshots missing.
    T-48h: opening → T-2h: current → T-0: closing (Pinnacle).
    """
    col = "odds_home" if bet_side in ("home", "1", "H") else "odds_away"
    return [
        {"opening_odd": opening_odd, col: opening_odd, "bookmaker": "open"},
        {"opening_odd": opening_odd, col: current_odd, "bookmaker": "mid"},
        {"opening_odd": opening_odd, col: closing_odd, "bookmaker": "pinnacle", "is_pinnacle": True},
    ]


def build_market_context(
    opportunity: Dict[str, Any],
    odds_ingestor: OddsIngestor,
    sport: str,
) -> Dict[str, Any]:
    event_id = str(opportunity.get("match_id", ""))
    history = odds_ingestor.get_odds_history(event_id, sport, hours=48.0)

    open_o = float(opportunity.get("opening_odd", opportunity.get("open_odd_home", 0)))
    current_o = float(opportunity.get("bookmaker_odds", open_o))
    close_o = float(
        opportunity.get("pinnacle_odds")
        or opportunity.get("pin_close_home")
        or current_o
    )

    if len(history) < 2 and open_o > 1.0:
        side = "home"
        po = opportunity.get("predicted_outcome", "1")
        if po in ("2", "A", "away"):
            side = "away"
        history = build_odds_history_from_lines(open_o, current_o, close_o, side)

    return {
        "odds_history": history,
        "hours_to_kickoff": float(opportunity.get("hours_to_kickoff", 12.0)),
        "predicted_closing_odds": close_o,
        "opening_odd": open_o,
        "current_odd": current_o,
        "line_movement_pct": (close_o / open_o - 1.0) if open_o > 1.0 else 0.0,
        "time_to_kickoff_minutes": float(opportunity.get("hours_to_kickoff", 12.0)) * 60,
    }
