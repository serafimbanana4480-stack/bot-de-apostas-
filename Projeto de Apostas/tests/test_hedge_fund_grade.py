import numpy as np
import pytest

from src.ingestion.result_settlement import ResultConsensusSettlement
from src.mlops.shadow_controller import LiveShadowController
from src.strategy_engine.portfolio_optimizer import MarkowitzPortfolioOptimizer


def test_result_consensus_settlement():
    """Test consensus scoring, discrepancies, and void game resolutions."""
    settler = ResultConsensusSettlement(required_agreement_count=2)
    
    # 1. Successful consensus: 2 out of 3 agree
    payloads = [
        {"source": "espn", "status": "FINISHED", "home_score": 100, "away_score": 95},
        {"source": "theoddsapi", "status": "FINISHED", "home_score": 100, "away_score": 95},
        {"source": "footballdata", "status": "FINISHED", "home_score": 98, "away_score": 95}
    ]
    res = settler.resolve_outcome("E01", payloads)
    assert res["status"] == "SETTLED"
    assert res["home_score"] == 100
    assert res["winner"] == "HOME"

    # 2. Void Consensus: 2 sources vote CANCELLED
    payloads_void = [
        {"source": "espn", "status": "CANCELLED"},
        {"source": "theoddsapi", "status": "CANCELLED"},
        {"source": "footballdata", "status": "FINISHED", "home_score": 0, "away_score": 0}
    ]
    res_void = settler.resolve_outcome("E02", payloads_void)
    assert res_void["status"] == "VOID"

    # 3. Discrepancy: All sources disagree
    payloads_discrep = [
        {"source": "espn", "status": "FINISHED", "home_score": 100, "away_score": 95},
        {"source": "theoddsapi", "status": "FINISHED", "home_score": 101, "away_score": 95},
        {"source": "footballdata", "status": "FINISHED", "home_score": 102, "away_score": 95}
    ]
    res_discrep = settler.resolve_outcome("E03", payloads_discrep)
    assert res_discrep["status"] == "DISCREPANCY"


def test_live_shadow_controller():
    """Test shadow logging and metrics discrepancy analysis."""
    controller = LiveShadowController("champ_v1", "chall_v2")
    
    # Simulate opportunity: both champion and challenger make predictions
    controller.process_live_opportunity(
        event_id="G1",
        current_odds=2.00,
        champ_prediction_func=lambda: 0.60, # EV: 0.20 -> BET
        chall_prediction_func=lambda: 0.62  # EV: 0.24 -> BET
    )
    
    # Opportunity with discrepancy
    controller.process_live_opportunity(
        event_id="G2",
        current_odds=2.00,
        champ_prediction_func=lambda: 0.48, # EV: -0.04 -> SKIP
        chall_prediction_func=lambda: 0.55  # EV: 0.10 -> BET
    )
    
    metrics = controller.get_shadow_performance_metrics()
    assert metrics["total_tracked"] == 2
    assert metrics["discrepancies"] == 1
    assert metrics["discrepancy_rate"] == 0.50


def test_markowitz_portfolio_optimizer():
    """Test covariance shrinkage and bounded quadratic Sharpe optimization."""
    optimizer = MarkowitzPortfolioOptimizer(risk_aversion_lambda=2.0, max_bet_exposure=0.08)
    
    bets = [
        {"event_id": "B1", "ev": 0.05, "bankroll": 1000.0},
        {"event_id": "B2", "ev": 0.08, "bankroll": 1000.0},
        {"event_id": "B3", "ev": -0.02, "bankroll": 1000.0}
    ]
    
    # 3x3 covariance matrix: B1 and B2 are moderately correlated
    cov_matrix = np.array([
        [0.010, 0.005, 0.000],
        [0.005, 0.015, 0.000],
        [0.000, 0.000, 0.010]
    ])
    
    shrunk_cov = optimizer.apply_covariance_shrinkage(cov_matrix, shrinkage_target=0.20)
    assert shrunk_cov[0, 1] == pytest.approx(0.004) # 0.005 * 0.8
    assert shrunk_cov[0, 0] == 0.010 # diagonal remains identical
    
    optimized = optimizer.optimize_allocation(bets, cov_matrix)
    
    assert len(optimized) == 3
    
    # Positive EV bets should get allocated stake weights
    assert optimized[0]["portfolio_weight"] > 0.0
    assert optimized[1]["portfolio_weight"] > 0.0
    # Negative EV bets should get zero weight
    assert optimized[2]["portfolio_weight"] == 0.0
    
    # Weights should be capped at max_bet_exposure (0.08)
    for bet_res in optimized:
        assert bet_res["portfolio_weight"] <= 0.08
