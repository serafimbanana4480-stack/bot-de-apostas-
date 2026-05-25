"""
Honest historical simulator — purged walk-forward + per-game open/close sharp money.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pandas as pd

from src.data.local_store import LocalDataStore
from src.pipeline.market_context import build_market_context
from src.simulation.metrics import compute_backtest_metrics
from src.validation.clv_tracker import CLVTracker
from src.validation.leakage_detector import LeakageDetector, LeakageError
from src.validation.walk_forward import WalkForwardValidator

if TYPE_CHECKING:
    from src.pipeline.sport_strategy import SportStrategy

logger = logging.getLogger(__name__)


class HonestHistoricalSimulator:
    def __init__(
        self,
        sport: str = "football",
        train_days: int = 180,
        test_days: int = 30,
        embargo_days: int = 7,
        min_edge: float = 0.02,
        data_dir: str = "data",
        check_leakage: bool = False,
        verbose: bool = False,
        use_sharp: bool = False,
        use_dynamic_ev: bool = False,
    ):
        self.sport = sport
        self.train_days = train_days
        self.test_days = test_days
        self.embargo_days = embargo_days
        self.min_edge = min_edge
        self.check_leakage = check_leakage
        self.verbose = verbose
        self.use_sharp = use_sharp
        self.use_dynamic_ev = use_dynamic_ev
        self.store = LocalDataStore(data_dir)
        self.clv = CLVTracker()
        self.leakage = LeakageDetector()
        self.split_checks: List[Dict[str, Any]] = []

    def _load_football_history(self) -> pd.DataFrame:
        # Prefer real Pinnacle open/close odds when available.
        # Fall back to synthetic backtest odds, then to football-data.org results-only data.
        df = self.store.load_matches("football_real_odds")
        if df.empty:
            df = self.store.load_matches("football_backtest")
        if df.empty:
            df = self.store.load_matches("football_fdo")
            if df.empty:
                raise RuntimeError(
                    "No football data available. Run:\n"
                    "  scripts/ingest_free_data.py --source football-data-co-uk --sport football\n"
                    "  scripts/ingest_free_data.py --source football-data --sport football\n"
                    "  scripts/generate_synthetic_odds.py  (optional, for backtest with synthetic odds)"
                )
        df["date"] = pd.to_datetime(df["date"])
        # Ensure odds columns exist for CLV calculation
        for col, fallback in [
            ("open_odd_home", "odd_1"),
            ("pin_close_home", "odd_1"),
            ("pin_close_draw", "odd_X"),
            ("pin_close_away", "odd_2"),
        ]:
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        return df.sort_values("date").reset_index(drop=True)

    def _validate_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        if self.check_leakage:
            check = self.leakage.enforce_or_raise(df, time_col="date", target_col="actual_outcome")
            # Ensure open != closing used as same signal without movement column
            if "open_odd_home" in df.columns and "pin_close_home" in df.columns:
                same = (df["open_odd_home"] == df["pin_close_home"]).mean()
                if same > 0.95:
                    raise LeakageError(
                        "open_odd_home identical to pin_close_home in >95% rows — no line movement for CLV"
                    )
            return check
        return self.leakage.validate_training_frame(df, "date", "actual_outcome")

    def _evaluate_bet(
        self,
        strategy: SportStrategy,
        row: pd.Series,
        probs: Dict[str, float],
        model_open_only: bool,
    ) -> Optional[Dict[str, Any]]:
        from src.ingestion.odds_ingestor import OddsIngestor

        open_odd = float(row.get("open_odd_home", row.get("odd_1", 2.0)))
        close_odd = float(row.get("pin_close_home", open_odd))
        edge = probs["1"] - (1.0 / open_odd)
        if edge < self.min_edge:
            return None

        opp = {
            "match_id": str(row.get("match_id", row.name)),
            "calibrated_prob": probs["1"],
            "bookmaker_odds": open_odd,
            "opening_odd": open_odd,
            "open_odd_home": open_odd,
            "pinnacle_odds": close_odd,
            "pin_close_home": close_odd,
            "predicted_outcome": "1",
            "edge": edge,
            "hours_to_kickoff": float(row.get("hours_to_kickoff", 12.0)),
            "liquidity_usd": 5000.0,
            "recommended_stake": 10.0,
        }
        ctx = build_market_context(opp, OddsIngestor(data_root=str(self.store.root)), self.sport)

        decision = "BET_NOW"
        reason = "model_only"
        if not model_open_only and (self.use_sharp or self.use_dynamic_ev):
            decided = strategy.decide(opp, ctx)
            decision = decided.get("decision", "NO_BET")
            reason = decided.get("decision_reason", "")
            if decision in ("WAIT", "NO_BET"):
                return {
                    "skipped": True,
                    "decision": decision,
                    "reason": reason,
                    "edge": edge,
                    "open_odd": open_odd,
                    "close_odd": close_odd,
                    "line_movement_home": row.get("line_movement_home"),
                    "sharp_score": (decided.get("market_signals") or {}).get("sharp", {}).get("sharp_score"),
                }

        won = row.get("actual_outcome") == "1"
        pnl = (open_odd - 1.0) if won else -1.0
        clv_res = self.clv.calculate_clv(
            open_odd,
            "home",
            {
                "home": row["pin_close_home"],
                "draw": row["pin_close_draw"],
                "away": row["pin_close_away"],
            },
            market_type="3-way",
        )
        return {
            "skipped": False,
            "match_id": row.get("match_id"),
            "date": row["date"],
            "edge": edge,
            "pnl_units": pnl,
            "won": won,
            "clv_pct": clv_res.get("clv_percentage", 0),
            "decision": decision,
            "reason": reason,
            "open_odd": open_odd,
            "close_odd": close_odd,
            "line_movement_home": float(row.get("line_movement_home", close_odd / open_odd - 1)),
        }

    def run(
        self,
        strategy: Optional[SportStrategy] = None,
        start_date: date = None,
        end_date: date = None,
    ) -> Dict[str, Any]:
        if self.sport != "football":
            return {"sport": self.sport, "error": "Football only", "bets": 0}

        start_date = start_date or date(2024, 1, 1)
        end_date = end_date or date(2024, 12, 31)

        df = self._load_football_history()
        filtered = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]
        if not filtered.empty:
            df = filtered
        check = self._validate_dataset(df)

        if strategy is None:
            from src.pipeline.sport_strategy import get_sport_strategy
            strategy = get_sport_strategy(
                "football",
                use_sharp=self.use_sharp,
                use_dynamic_ev=self.use_dynamic_ev,
                use_timing=self.use_dynamic_ev,
            )

        validator = WalkForwardValidator(
            train_window_days=self.train_days,
            test_window_days=self.test_days,
            embargo_days=self.embargo_days,
        )
        from src.ml.models.football_poisson import FootballPoissonModel

        all_bets: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        splits = validator.split_data(df, "date")

        for fold_i, split in enumerate(splits):
            train_end = split["train_end"]
            embargo_cutoff = train_end - timedelta(days=self.embargo_days)
            train = df[df["date"] < embargo_cutoff]
            test = split["test"]

            wf_check = self.leakage.verify_walk_forward_split(train, test, embargo_days=self.embargo_days)
            self.split_checks.append(wf_check)
            if self.check_leakage and not wf_check["passed"]:
                raise LeakageError(f"Fold {fold_i}: embargo gap {wf_check['gap_days']}d < {self.embargo_days}d")

            if self.verbose:
                logger.info("Fold %s train=%s test=%s gap=%sd", fold_i, len(train), len(test), wf_check["gap_days"])

            if len(train) < 30 or test.empty:
                continue

            model = FootballPoissonModel(use_dixon_coles=True)
            model.fit(train, calibrate=True)

            for _, row in test.iterrows():
                probs = model.predict_match_outcome(
                    row["home_team"], row["away_team"], apply_calibration=True
                )
                result = self._evaluate_bet(
                    strategy,
                    row,
                    probs,
                    model_open_only=not (self.use_sharp or self.use_dynamic_ev),
                )
                if result is None:
                    continue
                if result.get("skipped"):
                    skipped.append(result)
                else:
                    result["fold"] = fold_i
                    all_bets.append(result)

        wait_count = sum(1 for s in skipped if s.get("decision") == "WAIT")
        nobet_count = sum(1 for s in skipped if s.get("decision") == "NO_BET")

        if not all_bets:
            report = {
                "bets": 0,
                "skipped_total": len(skipped),
                "waits_skipped": wait_count,
                "nobet_skipped": nobet_count,
                "leakage_check": check,
                "wf_splits_passed": all(s.get("passed", True) for s in self.split_checks),
                "tier_b": {"sharp": self.use_sharp, "dynamic_ev": self.use_dynamic_ev},
            }
            if self.check_leakage:
                report["leakage_gate"] = "PASSED"
            self.store.save_report(report, f"backtest_{self.sport}_{start_date}_{end_date}")
            return report

        bets_df = pd.DataFrame(all_bets)
        metrics = compute_backtest_metrics(bets_df)

        report = {
            "sport": self.sport,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "train_days": self.train_days,
            "test_days": self.test_days,
            "embargo_days": self.embargo_days,
            "purged_walk_forward": True,
            "folds": len(splits),
            "skipped_total": len(skipped),
            "waits_skipped": wait_count,
            "nobet_skipped": nobet_count,
            "leakage_check": check,
            "wf_splits_passed": all(s.get("passed", True) for s in self.split_checks),
            "tier_b": {"sharp": self.use_sharp, "dynamic_ev": self.use_dynamic_ev},
            **metrics,
        }
        if self.check_leakage:
            report["leakage_gate"] = "PASSED" if check.get("passed") and report["wf_splits_passed"] else "FAILED"

        # Statistical significance gate
        total_bets = report.get("total_bets", 0)
        n_folds = report["folds"]
        tier_b_active = self.use_sharp and self.use_dynamic_ev
        report["statistical_confidence"] = {
            "reliable": n_folds >= 5 and total_bets >= 100,
            "min_folds_met": n_folds >= 5,
            "min_bets_met": total_bets >= 100,
            "tier_b_active": tier_b_active,
            "folds": n_folds,
            "total_bets": total_bets,
        }
        if not report["statistical_confidence"]["reliable"]:
            report["warning"] = (
                f"Low statistical confidence — {n_folds} fold(s), {total_bets} bet(s). "
                "Recommend >= 5 folds and >= 100 bets for reliable inference."
            )
            logger.warning("Backtest %s_%s: %s", self.sport, start_date, report["warning"])

        self.store.save_report(report, f"backtest_{self.sport}_{start_date}_{end_date}")
        if self.verbose:
            logger.info("Backtest: %s", report)
        return report
