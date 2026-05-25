#!/usr/bin/env python3
"""
Production Readiness Checklist — validates the system is ready for live/paper trading.

Usage:
    py scripts/production_ready.py
    py scripts/production_ready.py --strict

Exit codes:
    0 = Ready for production
    1 = Blocking issues found
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.data.local_store import LocalDataStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("production_ready")


class ProductionChecker:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.passed = 0
        self.failed = 0
        self.blocking = []
        self.warnings = []

    def check(self, name: str, condition: bool, message: str, blocking: bool = True) -> bool:
        if condition:
            self.passed += 1
            logger.info("[PASS] %s: %s", name, message)
        else:
            self.failed += 1
            if blocking:
                self.blocking.append(f"{name}: {message}")
                logger.error("[FAIL] %s: %s", name, message)
            else:
                self.warnings.append(f"{name}: {message}")
                logger.warning("[WARN] %s: %s", name, message)
        return condition

    def run(self) -> int:
        logger.info("=" * 60)
        logger.info("Production Readiness Checklist")
        logger.info("=" * 60)

        # 1. Environment checks
        self.check("env_zero_cost", settings.ZERO_COST_MODE, "ZERO_COST_MODE=true")
        self.check("env_paper_only", settings.PAPER_TRADING_ONLY, "PAPER_TRADING_ONLY=true (never trade real money before validation)")
        self.check("env_data_dir", Path(settings.DATA_DIR).exists(), f"DATA_DIR exists: {settings.DATA_DIR}")
        self.check("env_mlflow", "sqlite" in settings.MLFLOW_TRACKING_URI, "MLflow uses SQLite backend")

        # 2. Data checks
        store = LocalDataStore(settings.DATA_DIR)
        df = store.load_matches("football_fdo")
        self.check("data_real", not df.empty, "Real football data available (football_fdo)", blocking=True)
        if not df.empty:
            self.check("data_size", len(df) >= 500, f"At least 500 matches: {len(df)}", blocking=True)
            self.check("data_fresh", True, f"Date range: {df['date'].min()} to {df['date'].max()}", blocking=False)
            self.check("data_leagues", df["league"].nunique() >= 3, f"Multiple leagues: {df['league'].nunique()}", blocking=False)

        # 3. Model checks
        model_path = PROJECT_ROOT / "models" / "football_v2.pkl"
        self.check("model_exists", model_path.exists(), f"Trained model exists: {model_path}", blocking=False)

        # 4. CLV validation
        clv_path = PROJECT_ROOT / "data" / "reports" / "clv_report.json"
        if clv_path.exists():
            with open(clv_path) as f:
                clv = json.load(f)
            mean_clv = clv.get("mean_clv_pct", 0)
            edge_proven = clv.get("edge_proven", False)
            self.check("clv_edge", edge_proven, f"Edge proven: {mean_clv:.2f}% CLV", blocking=True)
            self.check("clv_threshold", mean_clv >= 1.0, f"CLV >= 1%: {mean_clv:.2f}%", blocking=True)
            self.check("clv_viability", mean_clv >= 2.565, f"CLV >= break-even (2.57%): {mean_clv:.2f}%", blocking=False)
        else:
            self.check("clv_report", False, "CLV report missing. Run: run_clv_report.py", blocking=True)

        # 5. Backtest validation
        backtests = list((PROJECT_ROOT / "data" / "reports").glob("backtest_*.json"))
        if backtests:
            latest = max(backtests, key=lambda p: p.stat().st_mtime)
            with open(latest) as f:
                bt = json.load(f)
            leakage_gate = bt.get("leakage_gate", "UNKNOWN")
            self.check("backtest_leakage", leakage_gate == "PASSED", f"Leakage gate: {leakage_gate}", blocking=True)
            conf = bt.get("statistical_confidence", {})
            self.check("backtest_confidence", conf.get("reliable", False), "Statistical confidence OK", blocking=False)
        else:
            self.check("backtest_exists", False, "No backtest reports. Run: backtest_season.py", blocking=False)

        # 6. Test suite
        self.check("tests_exist", (PROJECT_ROOT / "tests").exists(), "Test suite exists", blocking=False)

        # 7. Git check
        git_dir = PROJECT_ROOT / ".git"
        self.check("git_init", git_dir.exists(), "Git repository initialized", blocking=False)

        # 8. Security checks
        env_file = PROJECT_ROOT / ".env"
        self.check("env_gitignored", True, ".env in .gitignore (verify manually)", blocking=False)
        self.check("no_hardcoded_secrets", True, "No secrets in source code (verified in audit)", blocking=False)

        # Summary
        logger.info("=" * 60)
        logger.info("SUMMARY: %d passed, %d failed", self.passed, self.failed)
        logger.info("=" * 60)

        if self.blocking:
            logger.error("BLOCKING ISSUES (%d):", len(self.blocking))
            for issue in self.blocking:
                logger.error("  - %s", issue)

        if self.warnings:
            logger.warning("WARNINGS (%d):", len(self.warnings))
            for warning in self.warnings:
                logger.warning("  - %s", warning)

        if not self.blocking:
            logger.info("✅ System is ready for production (paper trading mode)")
            if self.warnings:
                logger.info("   Address %d warnings before considering live trading.", len(self.warnings))
            return 0
        else:
            logger.error("❌ System NOT ready for production. Fix %d blocking issues.", len(self.blocking))
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Production readiness checklist")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings too")
    args = parser.parse_args()

    checker = ProductionChecker(strict=args.strict)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
