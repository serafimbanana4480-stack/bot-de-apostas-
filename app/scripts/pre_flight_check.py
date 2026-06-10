#!/usr/bin/env python3
"""
Pre-Flight Check — Verificação obrigatória antes de QUALQUER execução com dinheiro real.

Este script verifica:
1. Nenhum dado mock presente
2. Dados reais disponíveis
3. Secrets configurados
4. Modelo calibrado (ECE < 0.05)
5. Backtest report válido
6. Paper trading ativo (PAPER_TRADING_ONLY=True)

Usage:
    py scripts/pre_flight_check.py
    py scripts/pre_flight_check.py --approve-real-money  # DANGEROUS
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.risk.go_live_validator import GoLiveValidator, GoLiveReport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pre_flight")


def main():
    parser = argparse.ArgumentParser(description="Pre-flight safety check")
    parser.add_argument("--report", type=str, default="models/optimized/backtest_report.json")
    parser.add_argument("--paper-log", type=str, help="Path to paper trading log")
    parser.add_argument("--approve-real-money", action="store_true", help="Bypass paper-only requirement")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("VBQ-UNIFIED PRE-FLIGHT SAFETY CHECK")
    print("=" * 70)

    validator = GoLiveValidator()
    report = validator.validate(
        report_path=args.report if Path(args.report).exists() else None,
        paper_trading_log=None,
        require_real_data=True,
    )

    if args.approve_real_money:
        report.warnings.append("REAL MONEY OVERRIDE ACTIVATED — PAPER_TRADING_ONLY bypassed")
        # Remove paper-only blocker if it exists
        report.blockers = [b for b in report.blockers if "PAPER_TRADING_ONLY" not in b]
        logger.warning("REAL MONEY MODE REQUESTED — MANUAL OVERRIDE ACTIVE")

    print("\n" + report.to_markdown())
    print("=" * 70)

    if report.passed:
        print("\n[PASS] System is CLEARED for operation.")
        if args.approve_real_money:
            print("[WARNING] REAL MONEY TRADING IS ACTIVE.")
        else:
            print("[INFO] Paper trading mode — no real money at risk.")
        sys.exit(0)
    else:
        print("\n[FAIL] System is BLOCKED. Resolve the following:")
        for b in report.blockers:
            print(f"  - {b}")
        sys.exit(1)


if __name__ == "__main__":
    main()
