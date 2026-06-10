#!/usr/bin/env python3
"""
Go-Live Check — Script de verificação obrigatória antes de apostas reais.

Este script BLOQUEIA o sistema se qualquer critério de segurança falhar.
Não é opcional. Corre antes de QUALQUER deploy com dinheiro real.

Usage:
    py scripts/go_live_check.py --report models/optimized/backtest_report.json
    py scripts/go_live_check.py --report models/optimized/backtest_report.json --paper-log data/paper_trading_log.parquet
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.risk.go_live_validator import GoLiveValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("go_live_check")


def main():
    parser = argparse.ArgumentParser(description="Go-Live Validation Gate")
    parser.add_argument("--report", type=str, required=True, help="Path to backtest_report.json")
    parser.add_argument("--paper-log", type=str, help="Path to paper trading log (parquet/csv)")
    parser.add_argument("--output", type=str, default="go_live_report.md", help="Output markdown report")
    parser.add_argument("--force", action="store_true", help="Skip validation (NOT RECOMMENDED)")
    args = parser.parse_args()

    if args.force:
        logger.warning("=" * 80)
        logger.warning("FORCE MODE: VALIDATION SKIPPED. THIS IS DANGEROUS.")
        logger.warning("=" * 80)
        print("\nFORCE MODE ACTIVATED. NO VALIDATION PERFORMED.\n")
        sys.exit(0)

    paper_log = None
    if args.paper_log:
        p = Path(args.paper_log)
        if p.exists():
            if p.suffix == ".parquet":
                paper_log = pd.read_parquet(p)
            elif p.suffix == ".csv":
                paper_log = pd.read_csv(p)
            else:
                logger.error("Unsupported paper log format: %s", p.suffix)
                sys.exit(1)
        else:
            logger.warning("Paper log not found: %s", args.paper_log)

    validator = GoLiveValidator()
    report = validator.validate(
        report_path=args.report,
        paper_trading_log=paper_log,
        require_real_data=True,
    )

    # Print report
    print("\n" + "=" * 80)
    print(report.to_markdown())
    print("=" * 80 + "\n")

    # Save markdown
    out_path = Path(args.output)
    out_path.write_text(report.to_markdown(), encoding="utf-8")
    logger.info("Report saved to %s", out_path)

    # Save JSON
    json_path = out_path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    logger.info("JSON report saved to %s", json_path)

    if report.passed:
        logger.info("GO-LIVE APPROVED")
        sys.exit(0)
    else:
        logger.error("GO-LIVE BLOCKED: %s", report.blockers)
        sys.exit(1)


if __name__ == "__main__":
    main()
