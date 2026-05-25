"""Tests for operational cost tracking."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from src.monitoring.operational_costs import CostBreakdown, OperationalCostMonitor, ProfitPeriod


class TestOperationalCostMonitor:
    def test_record_api_call(self):
        m = OperationalCostMonitor(cost_threshold_pct=999.0)
        m.record_api_call("odds", 0.01)
        report = m.get_report()
        assert report["cost_breakdown"]["api_fees"] == 0.01

    def test_record_bet_commission(self):
        m = OperationalCostMonitor(cost_threshold_pct=999.0)
        m.record_bet(stake=10.0, commission_rate=0.05, gross_pnl=2.0)
        report = m.get_report()
        assert report["num_bets"] == 1
        assert report["gross_profit"] == 2.0
        assert report["cost_breakdown"]["commissions"] == 0.5

    def test_cost_alert_triggered(self):
        m = OperationalCostMonitor(cost_threshold_pct=20.0)
        m.record_bet(stake=10.0, commission_rate=0.05, gross_pnl=2.0)
        m.record_monthly_subscription(50.0)
        report = m.get_report()
        assert report["alert"] is True

    def test_net_profit_calculation(self):
        m = OperationalCostMonitor(cost_threshold_pct=999.0)
        m.record_bet(stake=10.0, commission_rate=0.05, gross_pnl=2.0)
        m.record_api_call("odds", 0.01)
        m.record_fx_cost(0.15)
        report = m.get_report()
        expected_net = 2.0 - (0.5 + 0.01 + 0.15)
        assert report["net_profit"] == pytest.approx(expected_net, rel=1e-3)

    def test_cost_breakdown_total(self):
        cb = CostBreakdown(api_fees=1.0, commissions=2.0, fx_costs=0.5)
        assert cb.total == 3.5

    def test_profit_period_net(self):
        p = ProfitPeriod(
            period_start=None,
            period_end=None,
            gross_profit=100.0,
            costs=CostBreakdown(commissions=5.0, api_fees=2.0),
            turnover=1000.0,
        )
        assert p.net_profit == 93.0
        assert p.roi_net == 9.3
