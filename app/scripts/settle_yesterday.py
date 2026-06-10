#!/usr/bin/env python3
"""
Settlement worker — run daily after matches finish (cron 08:00).

  poetry run python scripts/settle_yesterday.py --sport football
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.accounting.pnl import FinancialAccountingEngine
from src.core.config import settings
from src.data.local_store import LocalDataStore
from src.ingestion.result_settlement import ResultConsensusSettlement
from src.pipeline.orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("settle_yesterday")


def settle_football_yesterday(store: LocalDataStore, settle_date: date) -> dict:
    from src.ingestion.result_fetcher import ResultFetcher

    fetcher = ResultFetcher()
    api_results = fetcher.fetch_football_results(settle_date)

    df = store.load_matches("football_real_odds")
    if df.empty:
        from src.ingestion.real_data_pipeline import ensure_real_data_exists
        try:
            path = ensure_real_data_exists(str(store.root))
            df = pd.read_parquet(path)
        except RuntimeError:
            return {"settled": 0, "reason": "no_match_data"}

    df["date"] = pd.to_datetime(df["date"])
    day_matches = df[df["date"].dt.date == settle_date]
    if day_matches.empty:
        return {"settled": 0, "reason": f"no_matches_on_{settle_date}"}

    settlement = ResultConsensusSettlement()
    ledger = FinancialAccountingEngine()
    settled_count = 0

    api_by_id = {r["event_id"]: r for r in api_results}

    for _, row in day_matches.iterrows():
        event_id = str(row.get("match_id", row.name))
        home_g = int(row["home_goals"])
        away_g = int(row["away_goals"])
        sources = [
            {"source": "local_db", "status": "FINISHED", "home_score": home_g, "away_score": away_g},
        ]
        if event_id in api_by_id:
            ar = api_by_id[event_id]
            sources.append({
                "source": ar.get("source", "api"),
                "status": "FINISHED",
                "home_score": ar["home_score"],
                "away_score": ar["away_score"],
            })
        else:
            sources.append(
                {"source": "local_consensus", "status": "FINISHED", "home_score": home_g, "away_score": away_g}
            )
        outcome = settlement.resolve_outcome(event_id, sources)
        if outcome.get("status") != "SETTLED":
            continue
        won = home_g > away_g
        ledger.record_transaction(
            event_id=event_id,
            stake=1.0,
            odds_predicted=row.get("odd_1", 2.0),
            odds_executed=row.get("odd_1", 2.0),
            won=won,
        )
        settled_count += 1

    report = {"date": settle_date.isoformat(), "settled": settled_count, "ledger_size": len(ledger.ledger)}
    store.save_report(report, f"settlement_{settle_date.isoformat()}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", default="football")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD, default yesterday")
    args = parser.parse_args()

    settle_date = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    store = LocalDataStore(settings.DATA_DIR)

    if args.sport == "football":
        report = settle_football_yesterday(store, settle_date)
    else:
        orch = PipelineOrchestrator(args.sport, mode="live")
        report = {"settled": 0, "note": "Use sport-specific settlement sources"}

    logger.info("Settlement report: %s", report)


if __name__ == "__main__":
    main()
