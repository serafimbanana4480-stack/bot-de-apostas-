import pytest
from src.ingestion.odds_collector import OddsCollector
from src.engine.market.odds_dynamics import OddsDynamicsModel

def test_odds_collector_requires_api_key():
    # Because we removed the mock, instantiating without setting the env var or passing a key should raise ValueError
    with pytest.raises(ValueError, match="ODDS_API_KEY is missing"):
        collector = OddsCollector()

def test_odds_dynamics_forecast():
    model = OddsDynamicsModel()
    # If time to kickoff is < 10 mins, it should return current odds
    result = model.forecast_closing_line(current_odds=2.0, time_to_kickoff_mins=5.0, historical_moves=[])
    assert result["predicted_closing_odds"] == 2.0
    assert result["confidence"] == 0.9
    
def test_steam_move_detection():
    model = OddsDynamicsModel()
    
    # 1. No moves
    assert not model.detect_sharp_money([])
    
    # 2. Steam move (5% drop)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    moves = [
        {"timestamp": now - timedelta(minutes=10), "odds": 2.0},
        {"timestamp": now, "odds": 1.85} # 1.85 is a 7.5% drop from 2.0
    ]
    assert model.detect_sharp_money(moves) == True
    
    # 3. No steam move (minor drop)
    moves_minor = [
        {"timestamp": now - timedelta(minutes=10), "odds": 2.0},
        {"timestamp": now, "odds": 1.98} # 1% drop
    ]
    assert model.detect_sharp_money(moves_minor) == False
