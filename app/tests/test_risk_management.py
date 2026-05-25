from datetime import datetime, timedelta

import pytest

from src.risk.portfolio_optimizer import PortfolioOptimizer
from src.risk.value_filter import ValueBetFilter


def test_value_bet_filter():
    """Tests that the Multi-Factor ValueBetFilter correctly validates opportunities."""
    vf = ValueBetFilter(min_edge=0.05, min_odd=1.50, min_probability=0.10)
    
    # 1. Perfect opportunity - should pass
    perfect_opp = {
        "match_id": "m1",
        "event_name": "FC Porto vs Sporting CP",
        "calibrated_prob": 0.70,
        "bookmaker_odds": 1.80, # implied prob = 55.5%, edge = 14.5%
        "pinnacle_odds": 1.78,
        "event_time": datetime.now() + timedelta(hours=12),
        "has_critical_injury_24h": False,
        "odds_2h_ago": 1.82, # tiny drop, completely acceptable
        "liquidity_usd": 15000.0,
        "min_liquidity_required": 1000.0,
        "historical_roi_positive": True
    }
    passed, reason = vf.evaluate(perfect_opp)
    assert passed is True
    assert reason is None

    # 2. Failing edge filter (edge = 42% - 1/2.5 = 2.0%, required 5%)
    low_edge_opp = perfect_opp.copy()
    low_edge_opp["bookmaker_odds"] = 2.50
    low_edge_opp["calibrated_prob"] = 0.42
    low_edge_opp["odds_2h_ago"] = 2.50
    passed, reason = vf.evaluate(low_edge_opp)
    assert passed is False
    assert "edge" in reason.lower()

    # 3. Failing odds filter (< 1.50)
    low_odds_opp = perfect_opp.copy()
    low_odds_opp["bookmaker_odds"] = 1.40
    passed, reason = vf.evaluate(low_odds_opp)
    assert passed is False
    assert "odds" in reason.lower()

    # 4. Critical Injury flag
    injury_opp = perfect_opp.copy()
    injury_opp["has_critical_injury_24h"] = True
    passed, reason = vf.evaluate(injury_opp)
    assert passed is False
    assert "injury" in reason.lower()

    # 5. Adverse Line Movement (> 3% drop in 2h)
    line_drop_opp = perfect_opp.copy()
    line_drop_opp["odds_2h_ago"] = 2.10 # 2.10 down to 1.80 is a 14% drop!
    passed, reason = vf.evaluate(line_drop_opp)
    assert passed is False
    assert "adverse" in reason.lower()


def test_value_bet_filter_hard_caps_longshots_and_uses_bin_thresholds():
    vf = ValueBetFilter(
        min_edge=0.03,
        min_odd=1.50,
        min_probability=0.10,
        max_odds=5.0,
        edge_threshold_by_bin={
            (1.0, 2.0): 0.02,
            (2.0, 3.0): 0.03,
            (3.0, 5.0): 0.05,
            (5.0, float("inf")): 0.10,
        },
        min_liquidity_proxy=1000.0,
    )

    longshot_opp = {
        "match_id": "m-long",
        "event_name": "Longshot FC vs Underdog United",
        "calibrated_prob": 0.20,
        "bookmaker_odds": 5.50,
        "pinnacle_odds": 5.30,
        "event_time": datetime.now() + timedelta(hours=12),
        "has_critical_injury_24h": False,
        "odds_2h_ago": 5.40,
        "liquidity_usd": 20000.0,
        "min_liquidity_required": 1000.0,
        "historical_roi_positive": True,
    }
    passed, reason = vf.evaluate(longshot_opp)
    assert passed is False
    assert "hard cap" in reason.lower()

    mid_bin_opp = longshot_opp.copy()
    mid_bin_opp["bookmaker_odds"] = 4.20
    mid_bin_opp["pinnacle_odds"] = 4.10
    mid_bin_opp["calibrated_prob"] = 0.28
    mid_bin_opp["odds_2h_ago"] = 4.20
    passed, reason = vf.evaluate(mid_bin_opp)
    assert passed is False
    assert "below threshold" in reason.lower()

    liquidity_opp = mid_bin_opp.copy()
    liquidity_opp["bookmaker_odds"] = 3.50
    liquidity_opp["pinnacle_odds"] = 3.45
    liquidity_opp["calibrated_prob"] = 0.40
    liquidity_opp["odds_2h_ago"] = 3.50
    liquidity_opp["liquidity_proxy"] = 500.0
    passed, reason = vf.evaluate(liquidity_opp)
    assert passed is False
    assert "liquidity proxy" in reason.lower()


def test_value_bet_filter_rejects_negative_historical_clv_for_high_bins():
    vf = ValueBetFilter(min_edge=0.03, min_probability=0.10, max_odds=5.0)
    opp = {
        "match_id": "m-bin",
        "event_name": "League X vs League Y",
        "calibrated_prob": 0.42,
        "bookmaker_odds": 3.60,
        "pinnacle_odds": 3.50,
        "event_time": datetime.now() + timedelta(hours=8),
        "has_critical_injury_24h": False,
        "odds_2h_ago": 3.60,
        "liquidity_usd": 10000.0,
        "min_liquidity_required": 1000.0,
        "historical_roi_positive": True,
        "historical_clv_pct_by_bin": {
            (3.0, 5.0): -1.25,
        },
    }
    passed, reason = vf.evaluate(opp)
    assert passed is False
    assert "historical clv" in reason.lower()

def test_portfolio_optimizer_scaling():
    """Tests Kelly allocation, drawdown scaling, and pro-rata daily exposure limits."""
    # Setup optimizer with $10,000 bankroll, max single bet 2%, max daily 5% for testing, 25% Kelly multiplier
    opt = PortfolioOptimizer(
        initial_bankroll=10000.0,
        max_daily_exposure_pct=0.05, # Max daily exposure $500 (5%)
        max_stake_per_bet_pct=0.02,  # Max single bet $200 (2%)
        kelly_multiplier=0.25,
        max_drawdown_limit_pct=0.20
    )

    opps = [
        {
            "match_id": "m1",
            "event_name": "Team A vs Team B",
            "calibrated_prob": 0.70,
            "bookmaker_odds": 2.0, # edge = 70% - 50% = 20%. Full Kelly = (0.7*1 - 0.3)/1 = 40%. Quarter Kelly = 10%. Drawdown-conditioned = 10%. capped at single-bet limit = 2%
            "pinnacle_odds": 1.98,
            "event_time": datetime.now() + timedelta(hours=6),
            "has_critical_injury_24h": False,
            "odds_2h_ago": 2.0,
            "liquidity_usd": 5000.0,
            "min_liquidity_required": 500.0,
            "historical_roi_positive": True
        },
        {
            "match_id": "m2",
            "event_name": "Team C vs Team D",
            "calibrated_prob": 0.80,
            "bookmaker_odds": 1.8, # edge = 80% - 55.5% = 24.5%. Quarter Kelly = ~13.7%. capped at single-bet limit = 2%
            "pinnacle_odds": 1.78,
            "event_time": datetime.now() + timedelta(hours=10),
            "has_critical_injury_24h": False,
            "odds_2h_ago": 1.8,
            "liquidity_usd": 5000.0,
            "min_liquidity_required": 500.0,
            "historical_roi_positive": True
        },
        {
            "match_id": "m3",
            "event_name": "Team E vs Team F",
            "calibrated_prob": 0.75,
            "bookmaker_odds": 2.0, # edge = 25%. Quarter Kelly = 12.5%. capped at single-bet limit = 2%
            "pinnacle_odds": 1.98,
            "event_time": datetime.now() + timedelta(hours=12),
            "has_critical_injury_24h": False,
            "odds_2h_ago": 2.0,
            "liquidity_usd": 5000.0,
            "min_liquidity_required": 500.0,
            "historical_roi_positive": True
        }
    ]

    # Total recommended is 2% + 2% + 2% = 6% which exceeds our daily limit of 5%.
    # The optimizer MUST apply pro-rata downscaling to keep total at exactly 5%!
    # Pro-rata ratio = 5% / 6% = 0.8333. Each bet gets 2% * 0.8333 = 1.6667% stake ($166.67).
    
    final_portfolio = opt.optimize_daily_portfolio(opps)
    
    assert len(final_portfolio) == 3
    total_stake_pct = sum(bet["final_kelly_fraction"] for bet in final_portfolio)
    assert total_stake_pct == pytest.approx(0.05, abs=1e-5)
    
    for bet in final_portfolio:
        assert bet["recommended_stake_usd"] == pytest.approx(166.67, abs=0.01)

def test_drawdown_circuit_breaker():
    """Tests that rolling drawdowns scale down Kelly allocations and trigger full halting."""
    opt = PortfolioOptimizer(
        initial_bankroll=10000.0,
        max_daily_exposure_pct=0.15,
        max_stake_per_bet_pct=0.02,
        kelly_multiplier=0.25,
        max_drawdown_limit_pct=0.20
    )

    opp = [{
        "match_id": "m1",
        "event_name": "Team A vs Team B",
        "calibrated_prob": 0.70,
        "bookmaker_odds": 2.0,
        "pinnacle_odds": 1.98,
        "event_time": datetime.now() + timedelta(hours=6),
        "has_critical_injury_24h": False,
        "odds_2h_ago": 2.0,
        "liquidity_usd": 5000.0,
        "min_liquidity_required": 500.0,
        "historical_roi_positive": True
    }]

    # Peak bankroll is 10k. Let's trigger a 10% drawdown (current bankroll 9k)
    opt.update_bankroll(9000.0)
    assert opt.get_current_drawdown() == 0.10
    
    # Sizing should scale down linearly. Drawdown scale factor = 1 - (10% / 20%) = 0.50.
    # Raw Kelly (10%) * Drawdown Scale (0.50) = 5%. capped at single-bet (2%) * scale = 1%.
    # (Since base capped single bet fraction is 2%, let's verify if the scaled fractional Kelly is capped properly)
    bets = opt.optimize_daily_portfolio(opp)
    assert len(bets) == 1
    # Raw Kelly was 10%. Scale is 0.5. Scaled raw Kelly is 5%.
    # The max single bet limit (2%) is applied to the scaled value. 
    # Let's check: final_kelly_fraction = min(scaled_kelly, max_stake_per_bet_pct) = min(5%, 2%) = 2%
    assert bets[0]["final_kelly_fraction"] == 0.02

    # Now let's trigger a >20% drawdown (current bankroll 7.5k)
    opt.update_bankroll(7500.0)
    assert opt.get_current_drawdown() == 0.25
    
    # Bets should be completely blocked by the circuit breaker!
    halted_bets = opt.optimize_daily_portfolio(opp)
    assert len(halted_bets) == 0
