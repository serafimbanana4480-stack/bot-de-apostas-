"""Tests for MissedOpportunityTracker."""
from __future__ import annotations

import tempfile

import pytest

from src.monitoring.missed_opportunity_tracker import MissedOpportunityTracker


def test_record_skip_and_miss():
    with tempfile.TemporaryDirectory() as td:
        tracker = MissedOpportunityTracker(log_dir=td)
        tracker.record_skip("e1", odds=2.1, predicted_prob=0.55,
                            recommended_stake=50, reason="EV too low")
        miss = tracker.record_result("e1", outcome="WIN", final_odds=2.1)
        assert miss is not None
        assert miss.missed_pnl == pytest.approx(55.0)  # (2.1-1)*50
        assert miss.reason == "EV too low"


def test_no_miss_on_loss():
    with tempfile.TemporaryDirectory() as td:
        tracker = MissedOpportunityTracker(log_dir=td)
        tracker.record_skip("e2", odds=2.0, predicted_prob=0.5, recommended_stake=10, reason="edge below threshold")
        miss = tracker.record_result("e2", outcome="LOSS")
        assert miss is None


def test_report_aggregation():
    with tempfile.TemporaryDirectory() as td:
        tracker = MissedOpportunityTracker(log_dir=td)
        tracker.record_skip("e3", odds=2.0, predicted_prob=0.5,
                            recommended_stake=10, reason="sharp drift")
        tracker.record_result("e3", outcome="WIN")
        tracker.record_skip("e4", odds=3.0, predicted_prob=0.4,
                            recommended_stake=20, reason="sharp drift")
        tracker.record_result("e4", outcome="WIN")
        report = tracker.generate_report()
        assert report["total_missed"] == 2
        # (2-1)*10 + (3-1)*20 = 10 + 40 = 50
        assert report["total_missed_pnl"] == pytest.approx(50.0)
        assert report["by_reason"]["sharp drift"]["count"] == 2


def test_persistence():
    with tempfile.TemporaryDirectory() as td:
        tracker = MissedOpportunityTracker(log_dir=td)
        tracker.record_skip("e5", odds=2.5, predicted_prob=0.6,
                            recommended_stake=100, reason="wait")
        # Simulate restart by creating new instance
        tracker2 = MissedOpportunityTracker(log_dir=td)
        miss = tracker2.record_result("e5", outcome="WIN")
        assert miss is not None
        assert miss.missed_pnl == pytest.approx(150.0)


def test_reset():
    with tempfile.TemporaryDirectory() as td:
        tracker = MissedOpportunityTracker(log_dir=td)
        tracker.record_skip("e6", odds=2.0, predicted_prob=0.5, recommended_stake=10, reason="x")
        tracker.reset()
        miss = tracker.record_result("e6", outcome="WIN")
        assert miss is None  # skip cleared by reset
