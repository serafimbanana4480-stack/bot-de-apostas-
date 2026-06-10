#!/usr/bin/env python3
"""
Unified pipeline entry point.

  poetry run python scripts/run_pipeline.py --sport football --mode live
  poetry run python scripts/run_pipeline.py --sport football --mode backtest --start 2024-01-01 --end 2024-12-31
  poetry run python scripts/run_pipeline.py --all --mode live
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_pipeline")


def main() -> None:
    parser = argparse.ArgumentParser(description="VBQ unified betting pipeline")
    parser.add_argument("--sport", choices=["football", "nba", "ufc", "mma"], default="football")
    parser.add_argument("--mode", choices=["live", "backtest"], default="live")
    parser.add_argument("--all", action="store_true", help="Run all sports")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD")
    parser.add_argument("--start", type=str, default="2024-01-01")
    parser.add_argument("--end", type=str, default="2024-12-31")
    parser.add_argument("--train-days", type=int, default=180)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--no-sharp", action="store_true")
    parser.add_argument("--no-dynamic-ev", action="store_true")
    parser.add_argument("--refresh-data", action="store_true")
    parser.add_argument("--check-leakage", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without placing real bets or persisting state")
    parser.add_argument("--shadow", action="store_true", help="Shadow deployment: run challenger in parallel without executing bets")
    args = parser.parse_args()

    if args.refresh_data:
        logger.info("Refreshing real data from football-data.co.uk...")
        from src.ingestion.real_data_pipeline import RealDataPipeline
        pipeline = RealDataPipeline()
        df = pipeline.build_training_dataset(
            seasons=["2223", "2324"],
            leagues=["E0", "E1", "D1", "D2", "F1", "F2", "I1", "I2", "N1", "P1"],
        )
        logger.info("Real data refreshed: %d matches", len(df))

    target = date.fromisoformat(args.date) if args.date else date.today()
    kwargs = dict(
        use_sharp=not args.no_sharp,
        use_dynamic_ev=not args.no_dynamic_ev,
        use_timing=not args.no_dynamic_ev,
        shadow_mode=args.shadow,
    )

    if args.dry_run:
        logger.info("DRY RUN MODE — No real bets will be placed, no state persisted")
        kwargs["dry_run"] = True

    if args.shadow:
        logger.info("SHADOW MODE — Challenger will run in parallel without executing bets")
        kwargs["dry_run"] = True

    if args.all:
        result = PipelineOrchestrator.run_all_sports(mode=args.mode, target_date=target, **kwargs)
    else:
        orch = PipelineOrchestrator(args.sport, mode=args.mode, **kwargs)
        if args.mode == "backtest":
            result = orch.run_backtest(
                date.fromisoformat(args.start),
                date.fromisoformat(args.end),
                train_days=args.train_days,
                test_days=args.test_days,
                check_leakage=args.check_leakage,
                verbose=True,
            )
        else:
            result = orch.run_daily(target, dry_run=args.dry_run)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
