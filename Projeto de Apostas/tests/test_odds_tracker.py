from datetime import datetime, timedelta

import pytest

from src.ingestion.odds_tracker import OddsLineTracker


def test_odds_tracker_line_movement():
    """Tests odds snapshot recording and 2-hour line movement calculations."""
    tracker = OddsLineTracker()
    match_id = "test_match_123"
    bookie = "pinnacle"
    
    # 1. Record an odds snapshot from 3 hours ago (reference point)
    now = datetime.now()
    three_hours_ago = now - timedelta(hours=3)
    
    # Simulating Pinnacle opening home odds at 2.0
    tracker.odds_history[match_id] = [
        {
            "timestamp": three_hours_ago,
            "bookmaker": bookie,
            "home_odds": 2.0,
            "away_odds": 1.90,
            "draw_odds": 3.40
        }
    ]
    
    # 2. Record current snapshot with odds dropping to 1.80 (heavy home backing / sharp money)
    # The drop is (1.80 - 2.0) / 2.0 = -10% change.
    tracker.record_odds_snapshot(
        match_id=match_id,
        bookmaker=bookie,
        home_odds=1.80,
        away_odds=2.10,
        draw_odds=3.60
    )
    
    # Check that both snapshots are recorded and pruned list has exactly 2 elements
    assert len(tracker.odds_history[match_id]) == 2
    
    # Calculate line movement over last 2 hours (which compares 1.80 with 2.0)
    change = tracker.get_line_movement_2h(match_id, bookie, outcome="home")
    assert change == pytest.approx(-0.10)
    
    # Test sharp money detection (default threshold is -3%, and -10% is below that)
    sharp_info = tracker.detect_sharp_money_move(match_id, threshold=-0.03)
    assert sharp_info["sharp_move_on_home"] is True
    assert sharp_info["sharp_move_on_away"] is False
    assert sharp_info["home_pinnacle_change_2h"] == pytest.approx(-0.10)

def test_odds_tracker_live_api_mock():
    """Tests the live odds retrieval in mock mode."""
    tracker = OddsLineTracker()
    data = tracker.fetch_live_market_odds(sport="soccer_epl")
    
    assert len(data) == 1
    match = data[0]
    assert match["home_team"] == "Arsenal"
    assert match["away_team"] == "Chelsea"
    
    # Check that Pinnacle, Betfair, and Bet365 are present
    bookies = [b["key"] for b in match["bookmakers"]]
    assert "pinnacle" in bookies
    assert "betfair_ex_eu" in bookies
    assert "bet365" in bookies
