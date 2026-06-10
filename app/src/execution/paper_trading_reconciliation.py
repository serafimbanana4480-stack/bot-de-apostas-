"""
Paper trading P&L reconciliation — compare simulated vs. actual results.

Tracks paper trades alongside real trades to validate the simulation model
before risking real capital.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("paper_trading_reconciliation")


@dataclass
class PaperTrade:
    """A single paper trade record."""
    trade_id: str
    event_id: str
    placed_at: datetime
    sport: str
    bet_type: str           # "back", "lay"
    selection: str          # Team/player name
    odds_placed: float      # Odds when bet was placed
    odds_simulated: float   # Expected closing odds from simulation
    stake: float
    simulated_pnl: float    # P&L according to simulation model
    actual_pnl: Optional[float] = None  # Real P&L (None until settled)
    settled: bool = False
    settled_at: Optional[datetime] = None
    result: Optional[str] = None  # "win", "loss", "void"

    @property
    def pnl_error(self) -> Optional[float]:
        """Difference between simulated and actual P&L."""
        if self.actual_pnl is None:
            return None
        return self.simulated_pnl - self.actual_pnl

    @property
    def pnl_error_pct(self) -> Optional[float]:
        """Percentage error of simulation."""
        if self.actual_pnl is None or self.actual_pnl == 0:
            return None
        return (self.pnl_error / abs(self.actual_pnl)) * 100


@dataclass
class ReconciliationReport:
    """Summary of paper vs. real trading performance."""
    period_start: date
    period_end: date
    total_trades: int = 0
    settled_trades: int = 0
    total_simulated_pnl: float = 0.0
    total_actual_pnl: float = 0.0
    trades: List[PaperTrade] = field(default_factory=list)

    @property
    def net_pnl_error(self) -> float:
        return self.total_simulated_pnl - self.total_actual_pnl

    @property
    def correlation(self) -> float:
        """Correlation between simulated and actual P&L."""
        if len(self.trades) < 2:
            return 0.0
        sim = np.array([t.simulated_pnl for t in self.trades])
        act = np.array([t.actual_pnl or 0.0 for t in self.trades])
        if np.std(sim) == 0 or np.std(act) == 0:
            return 0.0
        return float(np.corrcoef(sim, act)[0, 1])

    @property
    def rmse(self) -> float:
        """Root mean square error of simulation."""
        errors = [t.pnl_error for t in self.trades if t.pnl_error is not None]
        if not errors:
            return 0.0
        return float(np.sqrt(np.mean(np.square(errors))))

    @property
    def mape(self) -> float:
        """Mean absolute percentage error."""
        errors = [abs(t.pnl_error_pct) for t in self.trades if t.pnl_error_pct is not None]
        if not errors:
            return 0.0
        return float(np.mean(errors))

    @property
    def is_accurate(self) -> bool:
        """Simulation is accurate if correlation > 0.8 and MAPE < 20%."""
        return self.correlation > 0.8 and self.mape < 20.0


class PaperTradingReconciler:
    """
    Reconciles paper trades against real outcomes.

    Usage:
        reconciler = PaperTradingReconciler()
        trade = reconciler.place_paper_trade(
            event_id="123", odds=2.10, stake=10.0,
            expected_return=12.0, simulated_pnl=2.0,
        )
        # After result is known:
        reconciler.settle_trade(trade.trade_id, actual_pnl=1.80, result="win")
        report = reconciler.get_report()
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/paper_trading")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._trades: List[PaperTrade] = []
        self._load_trades()

    def _load_trades(self) -> None:
        """Load existing paper trades from disk."""
        trades_file = self.data_dir / "paper_trades.json"
        if trades_file.exists():
            try:
                with open(trades_file) as f:
                    raw = json.load(f)
                for t in raw.get("trades", []):
                    self._trades.append(self._dict_to_trade(t))
            except Exception as e:
                logger.warning("Could not load paper trades: %s", e)

    def _save_trades(self) -> None:
        """Persist paper trades to disk."""
        trades_file = self.data_dir / "paper_trades.json"
        try:
            raw = {
                "updated_at": datetime.now().isoformat(),
                "trades": [self._trade_to_dict(t) for t in self._trades],
            }
            with open(trades_file, "w") as f:
                json.dump(raw, f, indent=2, default=str)
        except Exception as e:
            logger.warning("Could not save paper trades: %s", e)

    @staticmethod
    def _dict_to_trade(d: Dict[str, Any]) -> PaperTrade:
        return PaperTrade(
            trade_id=d["trade_id"],
            event_id=d["event_id"],
            placed_at=datetime.fromisoformat(d["placed_at"]),
            sport=d["sport"],
            bet_type=d["bet_type"],
            selection=d["selection"],
            odds_placed=d["odds_placed"],
            odds_simulated=d["odds_simulated"],
            stake=d["stake"],
            simulated_pnl=d["simulated_pnl"],
            actual_pnl=d.get("actual_pnl"),
            settled=d.get("settled", False),
            settled_at=datetime.fromisoformat(d["settled_at"]) if d.get("settled_at") else None,
            result=d.get("result"),
        )

    @staticmethod
    def _trade_to_dict(t: PaperTrade) -> Dict[str, Any]:
        return {
            "trade_id": t.trade_id,
            "event_id": t.event_id,
            "placed_at": t.placed_at.isoformat(),
            "sport": t.sport,
            "bet_type": t.bet_type,
            "selection": t.selection,
            "odds_placed": t.odds_placed,
            "odds_simulated": t.odds_simulated,
            "stake": t.stake,
            "simulated_pnl": t.simulated_pnl,
            "actual_pnl": t.actual_pnl,
            "settled": t.settled,
            "settled_at": t.settled_at.isoformat() if t.settled_at else None,
            "result": t.result,
        }

    def place_paper_trade(
        self,
        event_id: str,
        sport: str,
        selection: str,
        bet_type: str,
        odds_placed: float,
        odds_simulated: float,
        stake: float,
        simulated_pnl: float,
    ) -> PaperTrade:
        """Record a new paper trade."""
        import uuid
        trade = PaperTrade(
            trade_id=str(uuid.uuid4())[:8],
            event_id=event_id,
            placed_at=datetime.now(),
            sport=sport,
            selection=selection,
            bet_type=bet_type,
            odds_placed=odds_placed,
            odds_simulated=odds_simulated,
            stake=stake,
            simulated_pnl=simulated_pnl,
        )
        self._trades.append(trade)
        self._save_trades()
        logger.info(
            "Paper trade placed: %s %s @ %.2f (sim P&L: %.2f)",
            selection, bet_type, odds_placed, simulated_pnl,
        )
        return trade

    def settle_trade(
        self,
        trade_id: str,
        actual_pnl: float,
        result: str,
    ) -> Optional[PaperTrade]:
        """Settle a paper trade with actual result."""
        for t in self._trades:
            if t.trade_id == trade_id:
                t.actual_pnl = actual_pnl
                t.result = result
                t.settled = True
                t.settled_at = datetime.now()
                self._save_trades()
                error = t.pnl_error
                logger.info(
                    "Trade %s settled: actual=%.2f simulated=%.2f error=%.2f",
                    trade_id, actual_pnl, t.simulated_pnl, error or 0.0,
                )
                return t
        logger.warning("Trade %s not found", trade_id)
        return None

    def get_report(self, days: Optional[int] = None) -> ReconciliationReport:
        """Generate reconciliation report."""
        cutoff = datetime.now() - __import__("datetime").timedelta(days=days or 9999)
        trades = [t for t in self._trades if t.placed_at >= cutoff]

        report = ReconciliationReport(
            period_start=min((t.placed_at.date() for t in trades), default=date.today()),
            period_end=max((t.placed_at.date() for t in trades), default=date.today()),
            total_trades=len(trades),
            settled_trades=sum(1 for t in trades if t.settled),
            total_simulated_pnl=sum(t.simulated_pnl for t in trades),
            total_actual_pnl=sum(t.actual_pnl or 0.0 for t in trades),
            trades=trades,
        )
        return report

    def print_report(self, days: Optional[int] = None) -> None:
        """Print human-readable reconciliation report."""
        r = self.get_report(days=days)
        logger.info("\n" + "=" * 70)
        logger.info("  Paper Trading Reconciliation Report")
        logger.info("=" * 70)
        logger.info(f"  Period:       {r.period_start} to {r.period_end}")
        logger.info(f"  Total trades: {r.total_trades} ({r.settled_trades} settled)")
        logger.info(f"  Simulated P&L: {r.total_simulated_pnl:+.2f}")
        logger.info(f"  Actual P&L:    {r.total_actual_pnl:+.2f}")
        logger.info(f"  Net error:     {r.net_pnl_error:+.2f}")
        logger.info(f"  Correlation:   {r.correlation:.3f}")
        logger.info(f"  RMSE:          {r.rmse:.2f}")
        logger.info(f"  MAPE:          {r.mape:.1f}%")
        logger.info(f"  Status:        {'PASS' if r.is_accurate else 'REVIEW NEEDED'}")
        logger.info("=" * 70 + "\n")
