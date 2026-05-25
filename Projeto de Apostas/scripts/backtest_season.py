#!/usr/bin/env python3
"""
Honest season backtest with leakage gate and Tier B comparison.

  py -3 scripts/backtest_season.py --sport football --season 2024 --check-leakage --verbose
  py -3 scripts/backtest_season.py --sport football --season 2024 --with-sharp --with-dynamic-ev
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.orchestrator import PipelineOrchestrator
from src.validation.leakage_detector import LeakageError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backtest_season")


def main() -> int:
    parser = argparse.ArgumentParser(description="Purged walk-forward season backtest")
    parser.add_argument("--sport", default="football")
    parser.add_argument("--season", type=int, default=None, help="Use full calendar year; omit if using --start/--end")
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--end", type=str, default=None)
    parser.add_argument("--train-days", type=int, default=180)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--embargo-days", type=int, default=7)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--check-leakage", action="store_true", help="Exit 1 if leakage detected")
    parser.add_argument("--with-sharp", action="store_true")
    parser.add_argument("--with-dynamic-ev", action="store_true")
    parser.add_argument("--compare-tier-b", action="store_true", help="Run baseline vs Tier B")
    args = parser.parse_args()

    if args.start and args.end:
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
    else:
        yr = args.season or 2024
        start = date(yr, 1, 1)
        end = date(yr, 12, 31)

    def run_once(sharp: bool, dynamic: bool, label: str) -> dict:
        orch = PipelineOrchestrator(
            args.sport,
            mode="backtest",
            use_sharp=sharp,
            use_dynamic_ev=dynamic,
            use_timing=dynamic,
            strict_leakage=args.check_leakage,
        )
        return orch.run_backtest(
            start, end,
            train_days=args.train_days,
            test_days=args.test_days,
            embargo_days=args.embargo_days,
            check_leakage=args.check_leakage,
            verbose=args.verbose,
        )

    try:
        if args.compare_tier_b:
            baseline = run_once(False, False, "baseline")
            tier_b = run_once(True, True, "tier_b")
            out = {
                "baseline": baseline,
                "tier_b": tier_b,
                "delta_roi": (tier_b.get("roi_per_bet", 0) - baseline.get("roi_per_bet", 0)),
                "delta_waits": tier_b.get("waits_skipped", 0),
            }
            print(json.dumps(out, indent=2, default=str))
            report = tier_b
        else:
            report = run_once(args.with_sharp, args.with_dynamic_ev, "single")
            print(json.dumps(report, indent=2, default=str))

        # Statistical confidence gate
        conf = report.get("statistical_confidence", {})
        if not conf.get("reliable", True):
            logger.warning("STATISTICAL CONFIDENCE LOW — %s", report.get("warning", ""))
            if conf.get("folds", 0) < 5:
                logger.warning("  -> Only %s fold(s); recommend >= 5 for walk-forward stability", conf.get("folds", 0))
            if conf.get("total_bets", 0) < 100:
                logger.warning("  -> Only %s bet(s); recommend >= 100 for meaningful ROI inference", conf.get("total_bets", 0))
            if not conf.get("tier_b_active", True):
                logger.warning("  -> Tier B is OFF (sharp=%s, dynamic_ev=%s); this reduces signal quality", args.with_sharp, args.with_dynamic_ev)

        if args.check_leakage:
            gate = report.get("leakage_gate", "PASSED" if report.get("wf_splits_passed", True) else "FAILED")
            if gate != "PASSED" and not report.get("leakage_check", {}).get("passed", True):
                logger.error("LEAKAGE GATE FAILED")
                return 1
            logger.info("LEAKAGE GATE PASSED (purged WF + embargo verified)")

        return 0

    except LeakageError as e:
        logger.error("Backtest aborted — leakage: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
