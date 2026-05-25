"""
Operational cost tracking — monitor API fees, commissions, FX costs.

Alerts when operational costs exceed a threshold (default 20%) of gross profit.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("operational_costs")


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a period."""
    api_fees: float = 0.0          # OddsAPI, Sportmonks, etc.
    commissions: float = 0.0        # Betfair/Pinnacle commission
    fx_costs: float = 0.0         # Currency conversion fees
    data_subscription: float = 0.0 # Monthly data fees
    compute_costs: float = 0.0     # Cloud/infra costs (optional)
    other: float = 0.0

    @property
    def total(self) -> float:
        return self.api_fees + self.commissions + self.fx_costs + self.data_subscription + self.compute_costs + self.other


@dataclass
class ProfitPeriod:
    """Profit and cost snapshot for a period."""
    period_start: date
    period_end: date
    gross_profit: float = 0.0      # Before costs
    costs: CostBreakdown = field(default_factory=CostBreakdown)
    num_bets: int = 0
    turnover: float = 0.0

    @property
    def net_profit(self) -> float:
        return self.gross_profit - self.costs.total

    @property
    def cost_pct(self) -> float:
        if self.gross_profit <= 0:
            return 0.0
        return (self.costs.total / self.gross_profit) * 100

    @property
    def roi_net(self) -> float:
        if self.turnover == 0:
            return 0.0
        return (self.net_profit / self.turnover) * 100


class OperationalCostMonitor:
    """
    Tracks operational costs and alerts when they exceed thresholds.

    Usage:
        monitor = OperationalCostMonitor(cost_threshold_pct=20.0)
        monitor.record_bet(stake=10.0, commission=0.05, gross_pnl=2.0)
        monitor.record_api_call(provider="oddsapi", cost=0.01)
        report = monitor.get_report()
        if report.alert:
            send_alert(f"Costs at {report.cost_pct:.1f}%")
    """

    def __init__(
        self,
        cost_threshold_pct: float = 20.0,
        data_dir: Optional[Path] = None,
        alert_callback: Optional[callable] = None,
    ):
        self.cost_threshold_pct = cost_threshold_pct
        self.data_dir = data_dir or Path("data/costs")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.alert_callback = alert_callback or self._default_alert

        # In-memory tracking for current session
        self._current_period = ProfitPeriod(
            period_start=date.today(),
            period_end=date.today(),
        )
        self._history: List[ProfitPeriod] = []
        self._load_history()

    def _default_alert(self, level: str, title: str, message: str, data: Optional[Dict] = None) -> None:
        logger.warning("ALERT [%s] %s: %s", level, title, message)

    def _load_history(self) -> None:
        """Load historical cost data from JSON."""
        hist_file = self.data_dir / "cost_history.json"
        if hist_file.exists():
            try:
                import json
                with open(hist_file) as f:
                    raw = json.load(f)
                for p in raw.get("periods", []):
                    self._history.append(self._dict_to_period(p))
            except Exception as e:
                logger.warning("Could not load cost history: %s", e)

    def _save_history(self) -> None:
        """Persist cost history to JSON."""
        hist_file = self.data_dir / "cost_history.json"
        try:
            import json
            raw = {
                "updated_at": datetime.now().isoformat(),
                "periods": [self._period_to_dict(p) for p in self._history + [self._current_period]],
            }
            with open(hist_file, "w") as f:
                json.dump(raw, f, indent=2, default=str)
        except Exception as e:
            logger.warning("Could not save cost history: %s", e)

    @staticmethod
    def _dict_to_period(d: Dict[str, Any]) -> ProfitPeriod:
        return ProfitPeriod(
            period_start=date.fromisoformat(d["period_start"]),
            period_end=date.fromisoformat(d["period_end"]),
            gross_profit=d.get("gross_profit", 0.0),
            costs=CostBreakdown(**d.get("costs", {})),
            num_bets=d.get("num_bets", 0),
            turnover=d.get("turnover", 0.0),
        )

    @staticmethod
    def _period_to_dict(p: ProfitPeriod) -> Dict[str, Any]:
        return {
            "period_start": p.period_start.isoformat(),
            "period_end": p.period_end.isoformat(),
            "gross_profit": p.gross_profit,
            "costs": {
                "api_fees": p.costs.api_fees,
                "commissions": p.costs.commissions,
                "fx_costs": p.costs.fx_costs,
                "data_subscription": p.costs.data_subscription,
                "compute_costs": p.costs.compute_costs,
                "other": p.costs.other,
            },
            "num_bets": p.num_bets,
            "turnover": p.turnover,
        }

    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------

    def record_bet(self, stake: float, commission_rate: float, gross_pnl: float) -> None:
        """Record a single bet's P&L and commission."""
        commission = stake * commission_rate
        self._current_period.gross_profit += gross_pnl
        self._current_period.costs.commissions += commission
        self._current_period.num_bets += 1
        self._current_period.turnover += stake
        self._check_alert()

    def record_api_call(self, provider: str, cost: float) -> None:
        """Record an API call cost."""
        self._current_period.costs.api_fees += cost
        self._check_alert()

    def record_fx_cost(self, amount: float) -> None:
        """Record FX conversion cost."""
        self._current_period.costs.fx_costs += amount
        self._check_alert()

    def record_monthly_subscription(self, amount: float) -> None:
        """Record monthly data subscription."""
        self._current_period.costs.data_subscription += amount
        self._check_alert()

    def _check_alert(self) -> None:
        """Trigger alert if costs exceed threshold."""
        if self._current_period.gross_profit > 0:
            cost_pct = self._current_period.cost_pct
            if cost_pct > self.cost_threshold_pct:
                self.alert_callback(
                    level="CRITICAL",
                    title="Operational Cost Alert",
                    message=f"Costs at {cost_pct:.1f}% of gross profit (threshold: {self.cost_threshold_pct:.1f}%)",
                    data={
                        "cost_pct": cost_pct,
                        "threshold": self.cost_threshold_pct,
                        "costs": self._current_period.costs,
                    },
                )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_report(self) -> Dict[str, Any]:
        """Generate current period report."""
        p = self._current_period
        return {
            "period": f"{p.period_start} to {p.period_end}",
            "gross_profit": round(p.gross_profit, 2),
            "total_costs": round(p.costs.total, 2),
            "net_profit": round(p.net_profit, 2),
            "cost_pct": round(p.cost_pct, 2),
            "roi_net": round(p.roi_net, 2),
            "num_bets": p.num_bets,
            "turnover": round(p.turnover, 2),
            "cost_breakdown": {
                "api_fees": round(p.costs.api_fees, 2),
                "commissions": round(p.costs.commissions, 2),
                "fx_costs": round(p.costs.fx_costs, 2),
                "data_subscription": round(p.costs.data_subscription, 2),
                "compute": round(p.costs.compute_costs, 2),
            },
            "alert": p.cost_pct > self.cost_threshold_pct,
        }

    def get_monthly_summary(self, months: int = 3) -> List[Dict[str, Any]]:
        """Get summary for last N months."""
        cutoff = date.today() - timedelta(days=30 * months)
        periods = [p for p in self._history if p.period_end >= cutoff]
        return [self._period_to_dict(p) for p in periods]

    def close_period(self) -> None:
        """Close current period and start a new one."""
        self._history.append(self._current_period)
        self._save_history()
        self._current_period = ProfitPeriod(
            period_start=date.today(),
            period_end=date.today(),
        )
        logger.info("Closed cost tracking period. History now has %d periods.", len(self._history))

    def export_csv(self, path: Optional[Path] = None) -> Path:
        """Export cost history to CSV."""
        import csv

        path = path or self.data_dir / f"costs_{date.today().isoformat()}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "period_start", "period_end", "gross_profit", "net_profit",
                "api_fees", "commissions", "fx_costs", "data_sub", "compute", "other",
                "total_costs", "cost_pct", "num_bets", "turnover",
            ])
            for p in self._history + [self._current_period]:
                writer.writerow([
                    p.period_start, p.period_end,
                    p.gross_profit, p.net_profit,
                    p.costs.api_fees, p.costs.commissions, p.costs.fx_costs,
                    p.costs.data_subscription, p.costs.compute_costs, p.costs.other,
                    p.costs.total, p.cost_pct, p.num_bets, p.turnover,
                ])
        logger.info("Exported cost history to %s", path)
        return path
