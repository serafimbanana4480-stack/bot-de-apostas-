import pytest

from src.ingestion.news_scraper import NewsInjuryParser
from src.mlops.drift_retraining import DriftRetrainingTrigger


def test_news_injury_parser():
    """Test extracting star player injuries and setting correct ELO rating penalties."""
    parser = NewsInjuryParser()
    
    # Test star player out
    star_res = parser.parse_injury_headline("LeBron James (Lakers) is ruled OUT tonight with ankle soreness.")
    assert star_res["player"] == "LeBron James"
    assert star_res["team"] == "Lakers"
    assert star_res["status"] == "OUT"
    assert star_res["tier"] == "STAR"
    # base OUT is -0.08, star multiplier is 1.5x -> -0.12
    assert star_res["rating_modifier"] == pytest.approx(-0.12)
    
    # Test role player questionable
    role_res = parser.parse_injury_headline("Alex Caruso (Bulls) is marked QUESTIONABLE with knee soreness.")
    assert role_res["player"] == "Alex Caruso"
    assert role_res["team"] == "Bulls"
    assert role_res["status"] == "QUESTIONABLE"
    assert role_res["tier"] == "ROLE_PLAYER"
    assert role_res["rating_modifier"] == pytest.approx(-0.02)


def test_drift_retraining_trigger():
    """Test warm up states and triggering ECE calibration drift retrains."""
    trigger = DriftRetrainingTrigger(window_size=5, max_ece_threshold=0.10, min_avg_clv_edge=0.01)
    
    # 1. Warm up verification
    res_warm = trigger.check_retraining_trigger()
    assert res_warm["status"] == "WARM_UP_PHASE"
    assert res_warm["trigger_retraining"] is False
    
    # 2. Add stable data (predictions close to outcomes, high CLV edge)
    for _ in range(5):
        trigger.record_match_result(predicted_prob=0.90, outcome_won=1, clv_edge=0.03)
        
    res_stable = trigger.check_retraining_trigger()
    assert res_stable["trigger_retraining"] is False
    
    # 3. Inject poor predictions (high ECE drift)
    # Predicted 90% chance but outcomes are all losses (0), CLV decays
    for _ in range(5):
        trigger.record_match_result(predicted_prob=0.95, outcome_won=0, clv_edge=-0.02)
        
    res_drift = trigger.check_retraining_trigger()
    assert res_drift["trigger_retraining"] is True
    assert res_drift["reason"] == "CALIBRATION_DRIFT" or res_drift["reason"] == "CLV_DECAY"
