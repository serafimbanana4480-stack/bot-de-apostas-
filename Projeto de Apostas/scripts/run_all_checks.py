#!/usr/bin/env python3
"""
Run All Checks — Executa todos os diagnósticos e gera relatório consolidado.

Usage:
    uv run python scripts/run_all_checks.py
"""
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("run_all_checks")


def run_command(cmd: list, description: str) -> dict:
    """Execute a command and capture results."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {description}")
    logger.info(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        success = result.returncode == 0
        if not success:
            logger.error(f"FAILED: {description}")
            logger.error(result.stderr[:500])
        else:
            logger.info(f"SUCCESS: {description}")
        return {
            "command": " ".join(cmd),
            "success": success,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[:500] if result.stderr else "",
        }
    except Exception as e:
        logger.error(f"ERROR running {description}: {e}")
        return {"command": " ".join(cmd), "success": False, "error": str(e)}


def main():
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    # 1. Run tests
    results["checks"]["pytest"] = run_command(
        ["uv", "run", "python", "-m", "pytest", "tests/", "-q", "--tb=short"],
        "Test Suite (pytest)"
    )

    # 2. Profit checker
    results["checks"]["profit_checker"] = run_command(
        ["uv", "run", "python", "scripts/profit_checker.py", "--backtest-report", "data/reports/backtest_football_2023-01-01_2024-12-31.json"],
        "Profit Checker"
    )

    # 3. Arbitrage detection (synthetic)
    results["checks"]["arbitrage"] = run_command(
        ["uv", "run", "python", "scripts/detect_arbitrage.py", "--mode", "synthetic", "--min-profit", "1.0"],
        "Arbitrage Detection (synthetic)"
    )

    # 4. Leakage check
    results["checks"]["leakage"] = run_command(
        ["uv", "run", "python", "-c", "from src.validation.leakage_detector import check_odds_leakage; print(check_odds_leakage('data/bronze/matches_football_real_odds.parquet'))"],
        "Data Leakage Check"
    )

    # 5. Ruff lint check (non-blocking)
    results["checks"]["ruff"] = run_command(
        ["uv", "run", "ruff", "check", "src/", "tests/", "--select=E,W,F", "-q"],
        "Code Quality (ruff)"
    )

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    all_pass = all(r["success"] for r in results["checks"].values())
    for name, r in results["checks"].items():
        status = "PASS" if r["success"] else "FAIL"
        logger.info(f"  {status}: {name}")

    # Save report
    out_path = Path(settings.DATA_DIR) / "reports" / f"all_checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\nFull report saved to: {out_path}")

    if not all_pass:
        logger.warning("\nSome checks failed. Review the report above.")
        sys.exit(1)
    else:
        logger.info("\nAll checks passed!")


if __name__ == "__main__":
    main()
