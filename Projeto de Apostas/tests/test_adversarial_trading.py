from datetime import datetime, timedelta

import numpy as np
import pytest

from src.decision_engine.audit_logger import DecisionAuditLogger
from src.risk.cvar_kelly import CVaR_KellyRiskManager
from src.simulations.information_arrival import StochasticInformationArrival
from src.simulations.stochastic_execution import StochasticExecutionSimulator


def test_stochastic_execution_simulator():
    """Verify stochastic slippage, rejection sigmoid thresholds, and partial fills."""
    np.random.seed(42)
    sim = StochasticExecutionSimulator(base_slippage=0.01, market_volatility=0.01, impact_coefficient=0.02)
    
    # 1. Slippage bounds
    odds = sim.simulate_slippage(requested_odds=2.00, stake=10.0, liquidity=100.0)
    assert odds >= 1.01
    assert odds <= 2.05 # low variance bounds
    
    # 2. Rejection probability scale (low ratio should have ~0 prob)
    p_reject_low = sim.calculate_rejection_probability(stake=5.0, liquidity=100.0)
    assert p_reject_low < 0.05
    
    # High ratio (stake exceeds depth) should have high rejection prob
    p_reject_high = sim.calculate_rejection_probability(stake=95.0, liquidity=100.0)
    assert p_reject_high > 0.80

    # 3. Simulate order execution
    exec_res = sim.simulate_order_execution(requested_odds=2.00, stake=100.0, liquidity=100.0)
    assert exec_res["status"] in ["REJECTED", "FILLED", "PARTIAL"]
    if exec_res["status"] == "PARTIAL":
        assert exec_res["filled_stake"] < 100.0


def test_stochastic_information_arrival():
    """Verify news arrival segments and prior odds adjustment timeline."""
    arrival = StochasticInformationArrival(news_announcement_delay_mins=30)
    
    kickoff = datetime.now() + timedelta(hours=10)
    timeline = arrival.simulate_odds_timeline(initial_odds=2.00, kickoff_time=kickoff, injury_severity=0.8)
    
    assert len(timeline) == 4
    assert timeline[0]["information_state"] == "NO_NEWS"
    assert timeline[1]["information_state"] == "RUMOR_RELEASED"
    assert timeline[2]["information_state"] == "PUBLIC_ANNOUNCED"
    assert timeline[3]["information_state"] == "CLOSING_LINE"
    
    # Verify prior odds adjustment (RUMOR_RELEASED odds must drift from initial)
    assert timeline[1]["odds"] > 2.00


def test_cvar_kelly_risk_manager():
    """Verify drawdown-conditioned sizing and Expected Shortfall returns estimation."""
    risk = CVaR_KellyRiskManager(initial_bankroll=100.0, max_drawdown_limit=0.20, max_cvar_limit=0.05)
    
    # Drawdown scaling: no drawdown -> scale is 1.0 (raw kelly is unchanged)
    scaled_1 = risk.calculate_drawdown_conditioned_kelly(0.10)
    assert scaled_1 == pytest.approx(0.10)
    
    # 10% drawdown (half of max drawdown limit) -> scale is 0.5 -> 0.10 kelly becomes 0.05
    risk.update_bankroll(90.0)
    scaled_2 = risk.calculate_drawdown_conditioned_kelly(0.10)
    assert scaled_2 == pytest.approx(0.05)

    # 20% drawdown -> scale is 0.0
    risk.update_bankroll(80.0)
    scaled_3 = risk.calculate_drawdown_conditioned_kelly(0.10)
    assert scaled_3 == 0.0
    
    # CVaR estimate check on normal distributions of returns
    # Worst alpha cases average loss check
    np.random.seed(42)
    sim_returns = np.random.normal(-0.02, 0.05, size=1000)
    cvar = risk.estimate_cvar(sim_returns)
    assert cvar > 0.0
    
    # Risk evaluation evaluates both drawdown sizing and CVaR caps
    res = risk.evaluate_wager_risk(raw_kelly=0.10, simulated_pnl_returns=sim_returns)
    assert "final_kelly" in res
    assert res["final_kelly"] <= 0.10


def test_decision_audit_logger():
    """Verify JSON traces recording and serialization capabilities."""
    logger = DecisionAuditLogger()
    
    feats = {"elo_diff": 50, "rest_diff": 2}
    risk_eval = {"final_kelly": 0.04, "estimated_cvar": 0.02}
    
    entry = logger.record_decision(
        event_id="E100",
        features=feats,
        predicted_prob=0.55,
        market_odds=2.00,
        kelly_fraction=0.04,
        risk_evaluation=risk_eval,
        decision_status="BET",
        reason="EV exceeds safety thresholds"
    )
    
    assert entry["event_id"] == "E100"
    assert entry["outcome"]["decision"] == "BET"
    
    js = logger.export_audit_trail_json()
    assert "E100" in js
    assert "elo_diff" in js
