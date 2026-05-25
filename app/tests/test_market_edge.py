import numpy as np
import pytest

from src.decision_engine.decision import DecisionIntelligenceEngine
from src.market.bookmaker_modeling import BookmakerBehaviorModel
from src.market.odds_dynamics import OddsDynamicsEngine, SharpMoneyDetector
from src.ml.training.advanced_pipeline import AdvancedTrainingPipeline
from src.simulations.market_simulator import MarketSimulator
from src.strategy.timing_engine import StrategyTimingEngine
from src.testing.betting_simulator_v2 import BettingSimulatorV2
from src.valuation.dynamic_ev import DynamicEVValuation


def test_odds_dynamics_and_sharp_money():
    """Test trend direction, closing line value forecasting, and smart money triggers."""
    ode = OddsDynamicsEngine()
    smd = SharpMoneyDetector()
    
    # Drifting trend: odds moved up significantly
    hist_drift = [1.50, 1.70, 2.10]
    trend_res = ode.predict_odds_trend(current_odds=2.10, odds_history=hist_drift, hours_to_kickoff=5.0)
    assert trend_res["trend"] == "DRIFT"
    
    # Sharp sentiment pushing closing line down
    predicted_close = ode.predict_closing_odds(current_odds=2.00, hours_to_kickoff=2.0, sharp_sentiment=-0.10)
    assert predicted_close == 1.90 # 2.00 * (1 - 0.05)
    
    clv_edge = ode.calculate_expected_clv_edge(current_odds=2.00, predicted_closing_odds=1.90)
    assert clv_edge == pytest.approx(0.0526, abs=0.001)

    # Reverse Line Movement: 70% public backing on home team, but odds drifted up
    rlm = smd.detect_reverse_line_movement(public_bet_percentage=0.70, odds_movement=0.02)
    assert rlm is True


def test_bookmaker_modeling():
    """Test margin decomposition and provider sensitivity scores."""
    bm = BookmakerBehaviorModel()
    
    # Decompose margin: home 2.0, away 2.0 -> margin = (1/2 + 1/2) - 1 = 0%
    margin = bm.decompose_margin(2.0, 2.0)
    assert margin == 0.0
    
    # Decompose margin with typical 5% house edge
    margin_5pct = bm.decompose_margin(1.90, 1.90)
    assert margin_5pct == pytest.approx(0.0526, abs=0.001)

    assert bm.get_responsiveness_score("pinnacle") == 0.95


def test_strategy_timing():
    """Test optimal entry time routing (BET_NOW vs WAIT)."""
    ste = StrategyTimingEngine()
    
    # Shortening trend -> bet immediately
    res_short = ste.evaluate_optimal_entry_time(hours_to_kickoff=6.0, predicted_trend="SHORTEN", current_odds=2.0, predicted_closing_odds=1.90)
    assert res_short["action"] == "BET_NOW"
    
    # Drifting trend with plenty of time -> wait
    res_wait = ste.evaluate_optimal_entry_time(hours_to_kickoff=6.0, predicted_trend="DRIFT", current_odds=1.85, predicted_closing_odds=1.95)
    assert res_wait["action"] == "WAIT"


def test_dynamic_ev():
    """Test EV calculation and decay over time."""
    dev = DynamicEVValuation()
    
    ev = dev.calculate_dynamic_ev(model_prob=0.55, current_odds=2.0)
    assert ev == pytest.approx(0.10)
    
    decay = dev.estimate_ev_decay_rate(current_ev=0.10, hours_to_kickoff=2.0, market_efficiency_score=0.90)
    assert decay > 0.0


def test_market_simulator():
    """Test synthetic odds trajectory generation."""
    sim = MarketSimulator(seed=100)
    odds = sim.simulate_odds_trajectory(initial_odds=2.00, hours_to_kickoff=4, steps_per_hour=2)
    assert len(odds) == 9 # 4 * 2 + 1 initial
    assert odds[0] == 2.00
    assert all(o >= 1.01 for o in odds)


def test_advanced_pipeline_fitness():
    """Test multi-objective fitness evaluation."""
    pipe = AdvancedTrainingPipeline()
    
    preds = np.array([0.60, 0.40, 0.70])
    actuals = np.array([1, 0, 1])
    clv_edges = np.array([0.05, -0.02, 0.08])
    returns = np.array([0.95, -1.0, 0.90])
    
    fit = pipe.evaluate_candidate_fitness(preds, actuals, clv_edges, returns)
    assert fit["fitness"] > 0.0
    assert fit["accuracy"] == 1.0


def test_betting_simulator_v2():
    """Test simulator V2 rejects, slippage, and PnL updates."""
    sim = BettingSimulatorV2(initial_bankroll=1000.0, commission_rate=0.05)
    
    # Set seed to force execute or reject outcomes
    np.random.seed(42)
    
    res = sim.simulate_bet(
        event_id="G1",
        predicted_prob=0.60,
        model_odds=2.00,
        actual_outcome_won=True,
        slippage_deviation=0.0,
        rejection_probability=0.0
    )
    assert res["status"] == "EXECUTED"
    assert res["net_profit"] > 0.0
    assert sim.bankroll > 1000.0


def test_decision_intelligence():
    """Test state routing machine."""
    die = DecisionIntelligenceEngine(min_ev_threshold=0.02)
    
    # High EV, plenty of liquidity, stable lines -> BET_NOW
    dec_ok = die.evaluate_decision(
        event_id="E1",
        predicted_probability=0.60,
        current_odds=2.00,
        predicted_closing_odds=1.98,
        hours_to_kickoff=1.5,
        liquidity_available=1000.0,
        required_stake=100.0
    )
    assert dec_ok["decision"] == "BET_NOW"
    assert dec_ok["allocated_stake"] == 100.0

    # Negative EV -> NO_BET
    dec_no = die.evaluate_decision(
        event_id="E2",
        predicted_probability=0.45,
        current_odds=2.00,
        predicted_closing_odds=1.98,
        hours_to_kickoff=1.5,
        liquidity_available=1000.0,
        required_stake=100.0
    )
    assert dec_no["decision"] == "NO_BET"
    
    # Expect lines to drift up, plenty of time -> WAIT
    dec_wait = die.evaluate_decision(
        event_id="E3",
        predicted_probability=0.60,
        current_odds=1.85,
        predicted_closing_odds=1.95,
        hours_to_kickoff=4.0,
        liquidity_available=1000.0,
        required_stake=100.0
    )
    assert dec_wait["decision"] == "WAIT"
