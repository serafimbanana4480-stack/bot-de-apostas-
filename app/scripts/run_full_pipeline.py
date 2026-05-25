#!/usr/bin/env python3
"""
VBQ Full Pipeline — One-command end-to-end workflow.

Usage:
    py scripts/run_full_pipeline.py --mode train          # Train + CLV report
    py scripts/run_full_pipeline.py --mode backtest       # Full backtest
    py scripts/run_full_pipeline.py --mode live           # Live paper trading
    py scripts/run_full_pipeline.py --mode all            # Train + backtest + daily
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("full_pipeline")


def run_cmd(cmd: list[str], description: str) -> dict:
    """Run a script and capture results."""
    logger.info("=" * 60)
    logger.info("Running: %s", description)
    logger.info("Command: %s", " ".join(cmd))
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    success = result.returncode == 0
    if not success:
        logger.error("FAILED: %s\n%s", description, result.stderr[-500:])
    else:
        logger.info("SUCCESS: %s", description)
    return {"success": success, "stdout": result.stdout, "stderr": result.stderr}


def train_phase(source: str = "mock") -> dict:
    """Train model and generate CLV report."""
    results = {}
    results["ingest"] = run_cmd(
        ["scripts/ingest_free_data.py", "--sport", "football", "--source", source],
        "Data ingestion"
    )
    results["train"] = run_cmd(
        ["scripts/train_bot.py", "football", "--source", source, "--walk-forward"],
        "Model training"
    )
    results["clv"] = run_cmd(
        ["scripts/run_clv_report.py"],
        "CLV report"
    )
    return results


def backtest_phase() -> dict:
    """Run walk-forward backtest with Tier B comparison."""
    return run_cmd(
        [
            "scripts/backtest_season.py",
            "--sport", "football",
            "--season", str(date.today().year),
            "--check-leakage",
            "--compare-tier-b",
        ],
        "Walk-forward backtest"
    )


def live_phase() -> dict:
    """Run live paper trading pipeline."""
    return run_cmd(
        ["scripts/run_pipeline.py", "--sport", "football", "--mode", "live"],
        "Live paper trading"
    )


def daily_phase() -> dict:
    """Generate daily report."""
    return run_cmd(
        ["scripts/daily_report.py"],
        "Daily report"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="VBQ Full Pipeline")
    parser.add_argument("--mode", choices=["train", "backtest", "live", "daily", "all"], default="train")
    parser.add_argument("--source", choices=["mock", "football-data"], default="mock")
    args = parser.parse_args()

    logger.info("VBQ Full Pipeline — mode=%s, source=%s", args.mode, args.source)
    logger.info("Python: %s", sys.version.split()[0])
    logger.info("Root: %s", PROJECT_ROOT)

    results = {}

    if args.mode in ("train", "all"):
        results["train"] = train_phase(args.source)

    if args.mode in ("backtest", "all"):
        results["backtest"] = backtest_phase()

    if args.mode in ("live", "all"):
        results["live"] = live_phase()

    if args.mode in ("daily", "all"):
        results["daily"] = daily_phase()

    # Summary
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    all_ok = True
    for phase, res in results.items():
        if isinstance(res, dict) and "success" in res:
            status = "OK" if res["success"] else "FAIL"
            if not res["success"]:
                all_ok = False
            logger.info("  %-12s: %s", phase, status)
        elif isinstance(res, dict):
            for sub, subres in res.items():
                status = "OK" if subres.get("success") else "FAIL"
                if not subres.get("success"):
                    all_ok = False
                logger.info("  %-12s/%s: %s", phase, sub, status)

    # Save report
    report_path = PROJECT_ROOT / "data" / "reports" / f"pipeline_run_{date.today().isoformat()}.json"
    with open(report_path, "w") as f:
        json.dump({k: str(v) for k, v in results.items()}, f, indent=2, default=str)
    logger.info("Report saved: %s", report_path)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
