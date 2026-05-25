import numpy as np
import pandas as pd

from src.explainability.explain import DecisionTracer
from src.feature_store.store import FeatureStoreRegistry
from src.mlops.drift.drift import calculate_ks_statistic, calculate_psi
from src.mlops.model_governance.governance import ModelGovernance
from src.mlops.retraining.retraining import RetrainingTrigger
from src.regimes.regimes import MarketRegimeDetector
from src.simulations.simulator import BankrollSimulator

# Import modules under test
from src.validation.calibration.calibration import PlattCalibrator, calculate_ece


def test_calibration_ece_and_platt():
    """Test Expected Calibration Error calculation and Platt Calibrator."""
    y_true = np.array([0, 0, 1, 1, 1, 0, 1, 1, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.75, 0.3, 0.85, 0.6, 0.4, 0.2])
    
    ece = calculate_ece(y_true, y_prob, n_bins=5)
    assert 0.0 <= ece <= 1.0
    
    calibrator = PlattCalibrator()
    calibrator.fit(y_prob, y_true)
    calibrated = calibrator.predict(y_prob)
    assert len(calibrated) == len(y_prob)
    assert np.all(calibrated >= 0.0) & np.all(calibrated <= 1.0)


def test_model_governance():
    """Test champion-challenger promotion validation gates."""
    gov = ModelGovernance()
    
    champ_metrics = {"brier": 0.19, "ece": 0.03, "sharpe": 1.5, "max_drawdown": 12.0}
    
    # Challenger matches or beats all requirements
    challenger_ok = {"brier": 0.18, "ece": 0.02, "sharpe": 1.8, "max_drawdown": 10.0}
    assert gov.validation_gate(challenger_ok, champ_metrics) is True
    
    # Challenger has high ECE
    challenger_bad_ece = {"brier": 0.18, "ece": 0.07, "sharpe": 1.8, "max_drawdown": 10.0}
    assert gov.validation_gate(challenger_bad_ece, champ_metrics) is False
    
    # Challenger has worse Brier score
    challenger_bad_brier = {"brier": 0.22, "ece": 0.02, "sharpe": 1.8, "max_drawdown": 10.0}
    assert gov.validation_gate(challenger_bad_brier, champ_metrics) is False


def test_retraining_trigger():
    """Test automated retraining trigger thresholds."""
    trigger = RetrainingTrigger(drift_threshold=0.20)
    
    baseline = {"brier": 0.18, "ece": 0.02, "psi": 0.05, "avg_clv_pct": 2.5}
    
    # No trigger needed
    current_ok = {"brier": 0.185, "ece": 0.03, "psi": 0.10, "avg_clv_pct": 2.0}
    assert trigger.should_retrain(current_ok, baseline) is False
    
    # Triggered by high drift (PSI)
    current_drift = {"brier": 0.185, "ece": 0.03, "psi": 0.25, "avg_clv_pct": 2.0}
    assert trigger.should_retrain(current_drift, baseline) is True
    
    # Triggered by negative CLV
    current_neg_clv = {"brier": 0.185, "ece": 0.03, "psi": 0.10, "avg_clv_pct": -0.5}
    assert trigger.should_retrain(current_neg_clv, baseline) is True


def test_drift_detection():
    """Test feature and prediction drift algorithms."""
    expected = np.random.normal(loc=0.0, scale=1.0, size=100)
    actual_no_drift = np.random.normal(loc=0.01, scale=1.0, size=100)
    actual_drift = np.random.normal(loc=1.5, scale=1.0, size=100)
    
    psi_low = calculate_psi(expected, actual_no_drift)
    psi_high = calculate_psi(expected, actual_drift)
    assert psi_low < psi_high
    
    ks_stat, p_val = calculate_ks_statistic(expected, actual_drift)
    assert 0.0 <= ks_stat <= 1.0
    assert p_val < 0.05  # Statistically significant drift


def test_feature_store_registry(tmp_path):
    """Test registering datasets and verification of schema hashes."""
    registry = FeatureStoreRegistry(registry_dir=str(tmp_path))
    
    df1 = pd.DataFrame({
        "elo_diff": [12.0, -5.0],
        "rest_diff": [1.0, 0.0],
        "win_rate_5_diff": [0.1, -0.2]
    })
    
    # Register dataset version
    meta = registry.register_dataset(df1, "1.0.0")
    assert meta["feature_version"] == "1.0.0"
    assert len(meta["columns"]) == 3
    
    # Verify parity with same dataframe schema
    assert registry.verify_parity(df1, "1.0.0") is True
    
    # Different schema structure (missing columns)
    df_diff = pd.DataFrame({
        "elo_diff": [12.0, -5.0]
    })
    assert registry.verify_parity(df_diff, "1.0.0") is False


def test_regime_and_explain():
    """Test NBA regime detection and decision tracing logic."""
    detector = MarketRegimeDetector()
    
    # B2B fatigue regime
    game_b2b = {"is_playoffs": False, "rest_diff": -2.0}
    regime = detector.detect_regime(game_b2b)
    assert regime == "B2B_FATIGUE"
    
    mod_prob = detector.get_regime_modifier(regime, 0.60)
    assert mod_prob < 0.60  # Modifiers reduce prob of fatigued teams
    
    # Decision Tracer check
    tracer = DecisionTracer()
    features = {"elo_diff": 120.0, "rest_diff": 2.0, "win_rate_5_diff": 0.15}
    trace = tracer.trace_decision(features, 0.65)
    
    assert trace["predicted_probability"] == 0.65
    assert trace["verdict"] == "STRONG_HOME"
    assert len(trace["contributions"]) > 0


def test_bankroll_simulator():
    """Test Monte Carlo bankroll simulation runs."""
    simulator = BankrollSimulator(n_simulations=100)
    
    probs = np.array([0.55, 0.60, 0.52, 0.58, 0.62])
    odds = np.array([2.0, 1.90, 2.10, 1.85, 1.75])
    stakes = np.array([0.02, 0.02, 0.02, 0.02, 0.02])
    
    results = simulator.run_simulation(probs, odds, stakes, initial_bankroll=1000.0)
    
    assert "mean_final_bankroll" in results
    assert "ruin_probability" in results
    assert "mean_max_drawdown_pct" in results
    assert 0.0 <= results["ruin_probability"] <= 1.0
