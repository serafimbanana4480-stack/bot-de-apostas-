from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from src.ingestion.schema_validator import OddsEvent
from src.ml.training.clv_objective import clv_objective, time_decay_weights
from src.mlops.fallback import ModelFallback
from src.risk.circuit_breaker import CircuitBreaker
from src.simulation.walkforward_backtest import PurgedWalkForwardBacktest


def test_walkforward_backtest_execution():
    """Verify purged walkforward chronological window execution and metrics."""
    backtest = PurgedWalkForwardBacktest(
        train_window_days=10, 
        embargo_days=2, 
        step_days=5, 
        decision_hours_before=1
    )
    
    # 20 days of mock games
    games_data = []
    base_date = datetime(2026, 11, 1)
    for i in range(25):
        games_data.append({
            "game_id": f"GM{i}",
            "game_date": base_date + timedelta(days=i),
            "home_team": "BOS" if i % 2 == 0 else "LAL",
            "away_team": "LAL" if i % 2 == 0 else "BOS",
            "home_score": 110,
            "away_score": 100
        })
    games_df = pd.DataFrame(games_data)
    
    odds_data = []
    for i in range(25):
        odds_data.append({
            "game_id": f"GM{i}",
            # Create a 5% CLV margin edge on even indices
            "home_odds": 1.80 if i % 2 == 0 else 2.10,
            "closing_odds": 1.70 if i % 2 == 0 else 2.10
        })
    odds_df = pd.DataFrame(odds_data)
    
    # Mock model: returns 60% home win probability
    def mock_decide(event_id, odds):
        return 0.60
        
    metrics = backtest.run(games_df, odds_df, mock_decide)
    
    assert metrics["total_bets"] > 0
    assert "roi" in metrics
    assert "avg_clv" in metrics
    assert "win_rate" in metrics


def test_clv_objective_and_time_decay():
    """Verify loss scaling of CLV objective and exponential weights calculation."""
    preds = np.array([0.65, 0.40])
    open_odds = np.array([2.0, 2.0])
    close_odds = np.array([1.80, 2.20]) # First bet closed shorter (CLV), second drifted (negative CLV)
    
    losses = clv_objective(preds, open_odds, close_odds)
    # First bet: edge is 0.65 - 0.5 = +0.15. CLV is log(1.8) - log(2.0) = -0.105.
    # Loss: -(0.15 * -0.105) = +0.015
    assert losses[0] > 0
    
    # Time decay
    dates = [datetime.now(), datetime.now() - timedelta(days=100)]
    weights = time_decay_weights(dates, decay_lambda=0.005)
    
    assert weights[0] == pytest.approx(1.0)
    assert weights[1] < 1.0
    # exp(-0.005 * 100) = exp(-0.5) = 0.606
    assert weights[1] == pytest.approx(0.6065, rel=1e-3)


def test_circuit_breaker_drawdown_limit():
    """Verify circuit breaker triggers system pause when drawdown reaches 10% limit."""
    breaker = CircuitBreaker(initial_bankroll=100.0, max_drawdown_limit=0.10)
    
    # Normal wager check
    check_proceed = breaker.validate_wager(10.0)
    assert check_proceed["action"] == "PROCEED"
    
    # Exceed safety buffer (requires 50 * 1.10 = 55.0 budget headroom)
    check_buffer = breaker.validate_wager(95.0)
    assert check_buffer["action"] == "ABORT"
    assert check_buffer["reason"] == "INSUFFICIENT_BALANCE_BUFFER"
    
    # Inject large loss of 15.0 (bankroll drops to 85.0 -> 15% drawdown)
    breaker.record_pnl_result(-15.0)
    assert breaker.is_paused is True
    
    # Subsequent wagers must be aborted immediately
    check_paused = breaker.validate_wager(5.0)
    assert check_paused["action"] == "ABORT"
    assert check_paused["reason"] == "CIRCUIT_BREAKER_ACTIVE"


def test_model_fallback():
    """Verify fallback defaults to baseline when champion outputs invalid probabilities."""
    fallback = ModelFallback(baseline_prob_func=lambda: 0.50)
    
    # Champ functions
    def champ_ok():
        return 0.75
    def champ_fails():
        raise RuntimeError("Model file not found")
    def champ_nan():
        return float("nan")
        
    assert fallback.predict_safe(champ_ok) == 0.75
    assert fallback.predict_safe(champ_fails) == 0.50
    assert fallback.predict_safe(champ_nan) == 0.50


def test_odds_schema_validation():
    """Verify Pydantic input schemas catch out-of-bound odds data."""
    # Valid odds event
    valid_event = OddsEvent(
        event_id="E001",
        odds_home=1.95,
        odds_away=1.85,
        timestamp=datetime.now()
    )
    assert valid_event.odds_home == 1.95
    
    # Invalid odds values (<= 1.0)
    with pytest.raises(ValidationError):
        OddsEvent(
            event_id="E002",
            odds_home=0.95,
            odds_away=1.95,
            timestamp=datetime.now()
        )
