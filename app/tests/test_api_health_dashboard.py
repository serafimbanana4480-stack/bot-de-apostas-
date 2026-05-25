"""Tests for APIHealthDashboard."""
from __future__ import annotations

import tempfile

from src.monitoring.api_health_dashboard import APIHealthDashboard


def test_record_and_report():
    with tempfile.TemporaryDirectory() as td:
        dash = APIHealthDashboard(log_dir=td)
        # Betfair: healthy
        dash.record("betfair", latency_ms=120, success=True)
        dash.record("betfair", latency_ms=150, success=True)
        # Pinnacle: degraded (9 success + 1 error = 10% error rate)
        for _ in range(9):
            dash.record("pinnacle", latency_ms=300, success=True)
        dash.record("pinnacle", latency_ms=800, success=False, error_type="TIMEOUT")
        report = dash.report()
        assert report["overall_status"] == "DEGRADED"
        apis = {a["api"]: a for a in report["apis"]}
        assert apis["betfair"]["status"] == "HEALTHY"
        assert apis["pinnacle"]["status"] == "DEGRADED"
        assert apis["pinnacle"]["error_rate_pct"] == 10.0


def test_latency_percentiles():
    with tempfile.TemporaryDirectory() as td:
        dash = APIHealthDashboard(log_dir=td)
        for i in range(100):
            dash.record("api", latency_ms=float(i * 10), success=True)
        report = dash.report()
        api = report["apis"][0]
        assert api["p95_latency_ms"] >= 900.0
        assert api["p99_latency_ms"] >= 980.0


def test_empty_report():
    with tempfile.TemporaryDirectory() as td:
        dash = APIHealthDashboard(log_dir=td)
        report = dash.report()
        assert report["overall_status"] == "HEALTHY"
        assert report["apis"] == []
