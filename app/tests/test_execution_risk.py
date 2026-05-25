import json
import os

import numpy as np

from src.execution.latency import LatencyBudgetTracker, OddMovementAnalyzer
from src.execution.limits_tracker import BookmakerLimitsTracker, StakeSplitter
from src.execution.order_tracker import OrderTracker
from src.execution.override import HumanOverrideLog
from src.execution.settlement import SettlementRulesEngine
from src.mlops.ab_testing.ab_engine import ABTestingEngine, SequentialTTest
from src.mlops.canary.canary import CanaryEvaluator
from src.mlops.monitoring.collapse_monitor import ModelCollapseMonitor
from src.simulations.conditional_risk import ConditionalRiskEngine


def test_order_tracker(tmp_path):
    """Test order logging, JSON schema mapping, and slippage."""
    log_file = os.path.join(tmp_path, "audit.jsonl")
    tracker = OrderTracker(audit_log_path=log_file)
    
    # Assert slippage
    slip = tracker.calculate_slippage(1.95, 1.90)
    assert round(slip, 2) == -0.05
    
    # Assert rejection handling
    rejection = tracker.handle_bet_rejection(100.0, 50.0, 1.90)
    assert rejection["action"] == "EXECUTE_REDUCED"
    assert rejection["stake"] == 50.0

    # Log a dummy decision
    tracker.log_decision({
        "event_id": "EV-TEST-12",
        "model_version": "v1.0",
        "predicted_prob": 0.55,
        "kelly_stake": 50.0,
        "final_stake": 50.0,
        "odds_available": 1.95,
        "odds_used": 1.90,
        "executed": True,
        "result_settled": False
    })
    
    assert os.path.exists(log_file)
    with open(log_file) as f:
        line = f.readline()
        data = json.loads(line)
        assert data["event_id"] == "EV-TEST-12"
        assert "input_features_hash" in data


def test_limits_and_splitter():
    """Test bookmaker exposure bounds and stake splitting logic."""
    tracker = BookmakerLimitsTracker(limit_per_bookmaker=500.0)
    tracker.record_bet("Pinnacle", 300.0)
    
    assert tracker.get_available_capacity("Pinnacle") == 200.0
    assert tracker.get_available_capacity("Betfair") == 500.0
    
    splitter = StakeSplitter(tracker)
    offers = {"Pinnacle": 1.95, "Betfair": 1.90}
    
    # Request a stake of 350. The best Pinnacle has only 200 capacity.
    # The remainder (150) should go to Betfair.
    splits = splitter.split_stake(350.0, offers)
    assert len(splits) == 2
    assert splits[0] == ("Pinnacle", 200.0)
    assert splits[1] == ("Betfair", 150.0)


def test_human_override():
    """Test Telegram-triggered manual override logs and performance evaluation."""
    override_log = HumanOverrideLog()
    
    override_log.record_override("EV-01", 100.0, 0.0, "SKIP", "Operator felt line moved away")
    override_log.record_override("EV-02", 50.0, 150.0, "RESIZE", "High confidence info received")
    
    # Settle overrides: EV-01 (Skipped but theoretically won at 2.0 odds)
    override_log.settle_override("EV-01", won=True, odds=2.0)
    # EV-02 (Resized to 150, actually won at 2.0 odds)
    override_log.settle_override("EV-02", won=True, odds=2.0)
    
    metrics = override_log.evaluate_override_performance()
    # EV-01: original pnl = 100, actual = 0. diff = -100
    # EV-02: original pnl = 50, actual = 150. diff = +100
    # Net impact = 0
    assert metrics["net_pnl_impact"] == 0.0
    assert metrics["total_overrides"] == 2.0


def test_model_collapse_monitor():
    """Test Shannon entropy and unique ratio checks for model decay."""
    monitor = ModelCollapseMonitor(entropy_threshold=0.5, unique_ratio_threshold=0.20)
    
    # Healthy distributions
    healthy_probs = [0.1, 0.8, 0.3, 0.9, 0.25, 0.77, 0.45, 0.85, 0.6, 0.12]
    res_healthy = monitor.evaluate_collapse(healthy_probs)
    assert res_healthy["collapse_detected"] is False
    
    # Flat 50% predictions (collapsed)
    collapsed_probs = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    res_collapsed = monitor.evaluate_collapse(collapsed_probs)
    assert res_collapsed["collapse_detected"] is True
    assert len(res_collapsed["reasons"]) > 0


def test_latency_budget_and_ev():
    """Test computational latency constraints and EV decay tracking."""
    tracker = LatencyBudgetTracker(budget_ms=100.0)
    
    import time
    start = time.time()
    # Dummy calculation
    time.sleep(0.01)
    res = tracker.measure_latency(start)
    assert res["elapsed_ms"] > 0
    assert res["budget_exceeded"] is False

    analyzer = OddMovementAnalyzer()
    decay = analyzer.estimate_ev_decay(0.55, 1.95, 1.85, 150.0)
    assert decay["initial_ev"] > decay["final_ev"]
    assert decay["ev_lost"] > 0


def test_ab_testing_significance():
    """Test deterministic A/B routing and Welchs t-test significance analysis."""
    engine = ABTestingEngine("champ", "chall", split_ratio=0.5)
    
    r1 = engine.route_event("GAME-1")
    r2 = engine.route_event("GAME-1")
    # Assert deterministic routing for identical game ids
    assert r1 == r2
    
    ttest = SequentialTTest()
    # Challenger B outperforms Champion A
    returns_a = np.array([-10, 20, -5, -2, 10, -8, 15, -4, 5, 2])
    returns_b = np.array([25, 30, 15, -5, 20, 10, 35, 18, 5, 22])
    
    res = ttest.evaluate_significance(returns_a, returns_b)
    assert "t_statistic" in res
    assert "p_value" in res
    assert res["mean_b"] > res["mean_a"]


def test_canary_evaluator():
    """Test offline canary simulator blocking bad candidate deployments."""
    evaluator = CanaryEvaluator(max_divergence_pct=30.0, max_simulated_loss_pct=3.0)
    
    champ_decisions = [{"executed": True}, {"executed": True}, {"executed": False}]
    
    # 1. Matching predictions (healthy challenger)
    chall_preds = np.array([0.65, 0.62, 0.35])
    odds = np.array([1.80, 1.90, 2.00])
    outcomes = np.array([1, 1, 0])
    
    res = evaluator.evaluate_canary(champ_decisions, chall_preds, odds, outcomes)
    assert res["deploy_approved"] is True
    
    # 2. Underperforming candidate (significant losses)
    outcomes_loss = np.array([0, 0, 0])
    res_loss = evaluator.evaluate_canary(champ_decisions, chall_preds, odds, outcomes_loss)
    assert res_loss["deploy_approved"] is False


def test_conditional_risk():
    """Test conditional drawdown and block bootstrap ruin checks."""
    risk = ConditionalRiskEngine(n_bootstrap_paths=50)
    
    # Drawdowns filtered by regime
    pnl = np.array([-10.0, 20.0, -30.0, 15.0, -10.0])
    regimes = ["PLAYOFFS", "STANDARD", "PLAYOFFS", "PLAYOFFS", "STANDARD"]
    
    cond_dd = risk.calculate_conditional_drawdown(pnl, regimes, "PLAYOFFS")
    assert cond_dd >= 0.0
    
    # Bootstrap ruin
    returns = np.array([-5.0, 15.0, -10.0, 25.0, -8.0, 3.0, -2.0, 12.0])
    ruin_prob = risk.bootstrap_ruin_probability(returns, block_size=3, initial_bankroll=100.0, num_bets=10)
    assert 0.0 <= ruin_prob <= 1.0


def test_settlement_rules():
    """Test cross-referencing multi-source settlement data validation."""
    engine = SettlementRulesEngine()
    
    source_a = {"game_id": "G-1", "home_score": 102, "away_score": 98, "status": "finished"}
    source_b = {"game_id": "G-1", "home_score": 102, "away_score": 98, "status": "finished"}
    
    res = engine.verify_and_settle(source_a, source_b)
    assert res["settled"] is True
    assert res["winner"] == "HOME"
    
    # Mismatched score should block settlement
    source_b_bad = {"game_id": "G-1", "home_score": 100, "away_score": 98, "status": "finished"}
    res_conflict = engine.verify_and_settle(source_a, source_b_bad)
    assert res_conflict["settled"] is False
    assert "Score mismatch conflict" in res_conflict["reason"]
