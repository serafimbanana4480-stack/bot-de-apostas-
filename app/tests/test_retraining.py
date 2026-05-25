"""Tests for RetrainingTrigger with CLV thresholds."""
from __future__ import annotations

from src.mlops.retraining.retraining import RetrainingTrigger


def test_psi_trigger():
    rt = RetrainingTrigger()
    assert rt.should_retrain({"psi": 0.25}, {"psi": 0.0, "brier": 0.1})


def test_brier_trigger():
    rt = RetrainingTrigger(brier_decline_tolerance=0.01)
    assert rt.should_retrain({"psi": 0.0, "brier": 0.15}, {"psi": 0.0, "brier": 0.10})


def test_ece_trigger():
    rt = RetrainingTrigger()
    assert rt.should_retrain({"psi": 0.0, "brier": 0.1, "ece": 0.10}, {"psi": 0.0, "brier": 0.1})


def test_clv_critical_trigger():
    rt = RetrainingTrigger(clv_critical_threshold=0.0)
    assert rt.should_retrain({"avg_clv_pct": -0.5}, {"brier": 0.1})


def test_clv_warning_does_not_trigger():
    rt = RetrainingTrigger(clv_warning_threshold=0.5, clv_critical_threshold=0.0)
    assert not rt.should_retrain({"avg_clv_pct": 0.3}, {"brier": 0.1})
    alerts = rt.evaluate({"avg_clv_pct": 0.3}, {"brier": 0.1})
    warning = [a for a in alerts if not a.triggered and a.metric == "avg_clv_pct"]
    assert len(warning) == 1
    assert "warning" in warning[0].reason.lower()


def test_clv_status_healthy():
    rt = RetrainingTrigger(clv_warning_threshold=0.5, clv_critical_threshold=0.0)
    assert rt.clv_status(1.36)["status"] == "HEALTHY"


def test_clv_status_critical():
    rt = RetrainingTrigger(clv_warning_threshold=0.5, clv_critical_threshold=0.0)
    assert rt.clv_status(-0.2)["status"] == "CRITICAL"


def test_clv_status_warning():
    rt = RetrainingTrigger(clv_warning_threshold=0.5, clv_critical_threshold=0.0)
    assert rt.clv_status(0.3)["status"] == "WARNING"


def test_no_trigger_healthy():
    rt = RetrainingTrigger()
    assert not rt.should_retrain(
        {"psi": 0.05, "brier": 0.10, "ece": 0.02, "avg_clv_pct": 1.5},
        {"brier": 0.10},
    )
