"""Backtest must trigger Tier B filters when open/close diverge."""
from src.decision_engine.market_aware import MarketAwareDecisionEngine
from src.pipeline.market_context import build_odds_history_from_lines


def test_line_history_triggers_sharp_block():
    history = build_odds_history_from_lines(2.0, 2.25, 2.30, "home")
    engine = MarketAwareDecisionEngine(use_sharp=True, use_dynamic_ev=False, use_timing=False)
    opp = {
        "match_id": "x1",
        "calibrated_prob": 0.55,
        "bookmaker_odds": 2.0,
        "opening_odd": 2.0,
        "edge": 0.08,
        "predicted_outcome": "1",
        "pinnacle_odds": 2.3,
        "liquidity_usd": 5000.0,
        "recommended_stake": 10.0,
        "hours_to_kickoff": 8.0,
    }
    ctx = {"odds_history": history, "hours_to_kickoff": 8.0, "predicted_closing_odds": 2.3}
    out = engine.decide(opp, ctx)
    assert out["decision"] in ("NO_BET", "WAIT")


def test_dynamic_ev_wait_on_drift():
    engine = MarketAwareDecisionEngine(use_sharp=False, use_dynamic_ev=True, use_timing=True)
    opp = {
        "match_id": "x2",
        "calibrated_prob": 0.56,
        "bookmaker_odds": 2.0,
        "opening_odd": 2.0,
        "edge": 0.07,
        "predicted_outcome": "1",
        "pinnacle_odds": 2.35,
        "liquidity_usd": 5000.0,
        "hours_to_kickoff": 10.0,
    }
    ctx = {
        "odds_history": build_odds_history_from_lines(2.0, 2.0, 2.35, "home"),
        "hours_to_kickoff": 10.0,
        "predicted_closing_odds": 2.35,
    }
    out = engine.decide(opp, ctx)
    assert out["decision"] == "WAIT"


def test_mock_data_has_line_movement():
    from src.ingestion.mock_football_data import generate_mock_football_data
    df = generate_mock_football_data(num_seasons=1, teams_per_league=6, seed=99)
    assert "open_odd_home" in df.columns
    assert "pin_close_home" in df.columns
    diff = (df["open_odd_home"] != df["pin_close_home"]).mean()
    assert diff > 0.15
