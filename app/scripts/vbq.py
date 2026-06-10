#!/usr/bin/env python3
"""
VBQ Unified CLI — single entry point for all operations.

Usage:
  vbq train football --source football-data --objective clv --walk-forward
  vbq backtest football --start 2024-01-01 --end 2024-12-31
  vbq trade football --mode live --paper
  vbq monitor --dashboard
  vbq backup --s3
  vbq status
  vbq doctor
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vbq")

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable


def cmd_train(args):
    """Train a model for a given sport."""
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "train_bot.py"),
        args.sport,
        "--source", args.source,
        "--objective", args.objective,
        "--data-dir", args.data_dir,
    ]
    if args.walk_forward:
        cmd.append("--walk-forward")
    if args.calibrate:
        cmd.append("--calibrate")
    logger.info("Running: %s", " ".join(cmd))
    sys.exit(subprocess.call(cmd))


def cmd_backtest(args):
    """Run a backtest for a given sport."""
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "run_real_backtest.py"),
        "--sport", args.sport,
        "--start", args.start,
        "--end", args.end,
    ]
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    logger.info("Running: %s", " ".join(cmd))
    sys.exit(subprocess.call(cmd))


def cmd_trade(args):
    """Run the live trading pipeline."""
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "run_pipeline.py"),
        "--sport", args.sport,
        "--mode", args.mode,
    ]
    if args.paper:
        os.environ["PAPER_TRADING_ONLY"] = "true"
        logger.info("PAPER TRADING MODE ENABLED")
    else:
        logger.warning("LIVE TRADING MODE - real money at risk!")
        if not args.yes:
            confirm = input("  Confirm LIVE trading? [y/N] ")
            if confirm.lower() != "y":
                logger.info("Aborted")
                return
        os.environ["PAPER_TRADING_ONLY"] = "false"

    logger.info("Running: %s", " ".join(cmd))
    sys.exit(subprocess.call(cmd))


def cmd_monitor(args):
    """Open monitoring dashboard or show status."""
    if args.dashboard:
        import webbrowser
        grafana_url = "http://localhost:3000"
        logger.info("Opening Grafana: %s", grafana_url)
        webbrowser.open(grafana_url)
        return

    print("\n=== VBQ System Status ===")
    print(f"  Mode:            {'PAPER' if settings.PAPER_TRADING_ONLY else 'LIVE'}")
    print(f"  Zero-cost:       {settings.ZERO_COST_MODE}")
    print(f"  Data dir:        {settings.DATA_DIR}")
    print(f"  MLflow:          {settings.MLFLOW_TRACKING_URI}")
    print(f"  Betfair sandbox: {settings.BETFAIR_SANDBOX}")
    print(f"  Kelly mult:      {settings.KELLY_MULTIPLIER}")
    print(f"  Max drawdown:    {settings.MAX_DRAWDOWN_PCT}%")
    print(f"  Ensemble:        {settings.ENSEMBLE_METHOD}")
    print()


def cmd_backup(args):
    """Run data backup."""
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "backup.py")]
    if args.no_git:
        cmd.append("--no-git")
    if args.s3:
        cmd.append("--s3")
    if args.gdrive:
        cmd.append("--gdrive")
    if args.restore:
        cmd.extend(["--restore", args.restore])
    sys.exit(subprocess.call(cmd))


def cmd_doctor(args):
    """Run system health check."""
    print("\n=== VBQ Doctor ===\n")

    checks = {
        "Python": sys.version.split()[0],
        "Data directory": os.path.exists(settings.DATA_DIR),
        "MLflow URI": settings.MLFLOW_TRACKING_URI,
        "Betfair APP_KEY": bool(settings.BETFAIR_APP_KEY),
        "Betfair CERT": os.path.exists(settings.BETFAIR_CERT_PATH) if settings.BETFAIR_CERT_PATH else False,
        "Betfair KEY": os.path.exists(settings.BETFAIR_KEY_PATH) if settings.BETFAIR_KEY_PATH else False,
        "Pinnacle ID": bool(settings.PINNACLE_CLIENT_ID),
        "Telegram token": bool(settings.TELEGRAM_BOT_TOKEN),
        "SMTP configured": bool(settings.SMTP_HOST),
        "Paper trading": settings.PAPER_TRADING_ONLY,
    }

    all_ok = True
    for name, value in checks.items():
        if isinstance(value, bool):
            icon = "OK" if value else "MISSING"
            if not value and name in ("Betfair APP_KEY", "Data directory"):
                all_ok = False
        else:
            icon = str(value)
        print(f"  {name:25s} {icon}")

    data_dir = os.path.join(os.getcwd(), settings.DATA_DIR)
    if os.path.exists(data_dir):
        parquet_count = sum(1 for _ in Path(data_dir).rglob("*.parquet"))
        csv_count = sum(1 for _ in Path(data_dir).rglob("*.csv"))
        print(f"  {'Parquet files':25s} {parquet_count}")
        print(f"  {'CSV files':25s} {csv_count}")

    docker_ok = os.system("docker info > /dev/null 2>&1") == 0
    print(f"  {'Docker':25s} {'OK' if docker_ok else 'NOT RUNNING'}")

    print()
    if all_ok:
        print("  System ready for operation.")
    else:
        print("  Some checks failed - review configuration.")
    print()


def cmd_clv(args):
    """Run CLV report."""
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "run_clv_report.py")]
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    sys.exit(subprocess.call(cmd))


def main():
    parser = argparse.ArgumentParser(
        prog="vbq",
        description="VBQ Unified CLI - Quantitative Value Betting System",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- train ---
    train_p = sub.add_parser("train", help="Train a model")
    train_p.add_argument("sport", choices=["football", "nba", "ufc"])
    train_p.add_argument("--source", default="football-data-co-uk", choices=["football-data", "football-data-co-uk", "parquet"])
    train_p.add_argument("--objective", default="logloss", choices=["logloss", "clv"])
    train_p.add_argument("--walk-forward", action="store_true")
    train_p.add_argument("--calibrate", action="store_true", default=True)
    train_p.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))

    # --- backtest ---
    bt_p = sub.add_parser("backtest", help="Run a backtest")
    bt_p.add_argument("sport", choices=["football", "nba", "ufc"])
    bt_p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    bt_p.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    bt_p.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))

    # --- trade ---
    trade_p = sub.add_parser("trade", help="Run live/paper trading")
    trade_p.add_argument("sport", choices=["football", "nba", "ufc"])
    trade_p.add_argument("--mode", default="live", choices=["live", "paper"])
    trade_p.add_argument("--paper", action="store_true", help="Force paper trading")
    trade_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # --- monitor ---
    mon_p = sub.add_parser("monitor", help="Monitoring & status")
    mon_p.add_argument("--dashboard", action="store_true", help="Open Grafana in browser")

    # --- backup ---
    backup_p = sub.add_parser("backup", help="Data backup")
    backup_p.add_argument("--no-git", action="store_true")
    backup_p.add_argument("--s3", action="store_true")
    backup_p.add_argument("--gdrive", action="store_true")
    backup_p.add_argument("--restore", nargs="?", const="latest", default=None)

    # --- doctor ---
    sub.add_parser("doctor", help="System health check")

    # --- clv ---
    clv_p = sub.add_parser("clv", help="Run CLV report")
    clv_p.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "train": cmd_train,
        "backtest": cmd_backtest,
        "trade": cmd_trade,
        "monitor": cmd_monitor,
        "backup": cmd_backup,
        "doctor": cmd_doctor,
        "clv": cmd_clv,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
