"""
Daily Reconciliation Script.

Compares executed/paper-traded odds against the odds that were available
at the time of the signal, auditing slippage and P&L divergence.
"""
import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.core.config import settings

logger = logging.getLogger("daily_reconciliation")


def load_daily_report(target_date: date) -> Dict[str, Any]:
    path = Path(settings.DATA_DIR) / "reports" / f"daily_football_{target_date.isoformat()}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def reconcile(report: Dict[str, Any]) -> Dict[str, Any]:
    decisions = report.get("decisions", [])
    if not decisions:
        return {"status": "no_data", "date": report.get("date")}

    bets = [d for d in decisions if d.get("decision") in ("BET_NOW", "BET")]
    reconciled = []
    total_slippage_bps = 0.0
    missing_odds = 0

    for bet in bets:
        event_id = bet.get("match_id", "unknown")
        predicted_prob = bet.get("calibrated_prob", 0)
        signal_odds = bet.get("bookmaker_odds", 0)
        executed_odds = bet.get("effective_odds", signal_odds)

        slippage_bps = 0.0
        if signal_odds > 0 and executed_odds > 0:
            slippage_bps = (signal_odds - executed_odds) / signal_odds * 10000

        total_slippage_bps += max(0, slippage_bps)
        if not executed_odds:
            missing_odds += 1

        reconciled.append({
            "event_id": event_id,
            "predicted_prob": predicted_prob,
            "signal_odds": signal_odds,
            "executed_odds": executed_odds,
            "slippage_bps": round(slippage_bps, 2),
            "decision": bet.get("decision"),
        })

    n = len(bets)
    summary = {
        "date": report.get("date"),
        "total_signals": len(decisions),
        "bets_placed": n,
        "avg_slippage_bps": round(total_slippage_bps / n, 2) if n else 0,
        "missing_executed_odds": missing_odds,
        "reconciled_bets": reconciled,
    }
    return summary


def main():
    target = date.today() - timedelta(days=1)
    report = load_daily_report(target)
    if not report:
        logger.info("No daily report found for %s", target)
        return

    result = reconcile(report)
    out_path = Path(settings.DATA_DIR) / "reports" / f"reconciliation_{target.isoformat()}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(
        "Reconciliation for %s: bets=%d avg_slippage=%.1fbps missing_odds=%d",
        target, result["bets_placed"], result["avg_slippage_bps"], result["missing_executed_odds"]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
