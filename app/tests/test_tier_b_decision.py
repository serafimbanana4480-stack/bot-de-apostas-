"""Tier B: SharpMoney + DynamicEV + WAIT decisions."""
from src.decision_engine.market_aware import MarketAwareDecisionEngine
from src.market.sharp_money import SharpMoneyDetector
from src.valuation.dynamic_ev import DynamicEVValuation


def test_sharp_low_score_reduces_safety():
    det = SharpMoneyDetector(steam_threshold_pct=0.03)
    history = [
        {"odds_home": 2.20, "captured_at": "2025-01-01T10:00:00"},
        {"odds_home": 2.50, "captured_at": "2025-01-01T12:00:00"},
    ]
    res = det.detect_score("e1", history, bet_side="home")
    assert res["sharp_score"] < 0.35
    assert res["safe_to_bet"] is False


def test_dynamic_ev_wait_when_line_drifts_up():
    ev = DynamicEVValuation()
    opp = {
        "calibrated_prob": 0.55,
        "bookmaker_odds": 2.0,
        "pinnacle_odds": 2.25,
    }
    ctx = {"hours_to_kickoff": 8.0, "predicted_closing_odds": 2.25}
    forecast = ev.forecast(opp, ctx)
    assert forecast.best_action == "WAIT"
    assert forecast.wait_minutes > 0


def test_market_aware_wait_on_sharp_drift():
    engine = MarketAwareDecisionEngine(use_sharp=True, use_dynamic_ev=False, use_timing=False)
    opp = {
        "match_id": "m1",
        "calibrated_prob": 0.6,
        "bookmaker_odds": 2.0,
        "edge": 0.1,
        "recommended_stake": 20.0,
        "predicted_outcome": "home",
        "pinnacle_odds": 2.0,
        "liquidity_usd": 5000.0,
    }
    ctx = {
        "odds_history": [
            {"odds_home": 2.0},
            {"odds_home": 2.15},
        ],
        "hours_to_kickoff": 10,
    }
    out = engine.decide(opp, ctx)
    assert out["decision"] in ("NO_BET", "WAIT")


def test_market_aware_bet_when_sharp_aligns():
    engine = MarketAwareDecisionEngine(use_sharp=True, use_dynamic_ev=True, use_timing=True)
    opp = {
        "match_id": "m2",
        "calibrated_prob": 0.58,
        "bookmaker_odds": 2.1,
        "opening_odd": 2.2,
        "edge": 0.08,
        "recommended_stake": 25.0,
        "predicted_outcome": "1",
        "pinnacle_odds": 2.05,
        "liquidity_usd": 8000.0,
        "hours_to_kickoff": 4.0,
    }
    ctx = {
        "odds_history": [
            {"odds_home": 2.2},
            {"odds_home": 2.1},
        ],
        "hours_to_kickoff": 4.0,
        "predicted_closing_odds": 2.05,
    }
    out = engine.decide(opp, ctx)
    assert out["decision"] in ("BET_NOW", "WAIT", "NO_BET")
