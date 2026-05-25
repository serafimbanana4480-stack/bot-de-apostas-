#!/usr/bin/env python3
"""
Ingest FREE data sources into local Parquet lake (0€).

Usage:
  poetry run python scripts/ingest_free_data.py --sport football --source mock
  poetry run python scripts/ingest_free_data.py --sport football --source football-data
  poetry run python scripts/ingest_free_data.py --sport nba
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.local_store import LocalDataStore
from src.ingestion.football_data_co_uk import FootballDataCoUkClient
from src.ingestion.football_data_org import FootballDataOrgClient
from src.ingestion.mock_football_data import ensure_mock_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_free_data")


def _apply_date_window(df: pd.DataFrame, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    if df.empty or ("date" not in df.columns):
        return df
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if start:
        out = out[out["date"] >= pd.to_datetime(start)]
    if end:
        out = out[out["date"] <= pd.to_datetime(end)]
    return out.sort_values("date").reset_index(drop=True)


def _drop_real_odds_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the football-data.org training slice free of closing-odds leakage."""
    cols_to_drop = ["odd_1", "odd_X", "odd_2", "closing_odd", "pin_close_home", "pin_close_draw", "pin_close_away"]
    keep = [c for c in cols_to_drop if c in df.columns]
    if not keep:
        return df
    return df.drop(columns=keep)


def ingest_football_mock(store: LocalDataStore) -> int:
    df = ensure_mock_dataset(str(store.root), force=False)
    store.save_matches(df, source="football_mock")
    # Keep the historical backtest alias in sync for scripts that still read it.
    store.save_matches(df, source="football_backtest")
    csv_path = store.root / "mock_football.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Mock football: %s matches", len(df))
    return len(df)


def ingest_football_data_org(
    store: LocalDataStore,
    leagues: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    rate_limit_delay: float = 6.0,
) -> int:
    codes = [c.strip() for c in leagues.split(",")]
    token = os.getenv("FOOTBALL_DATA_ORG_TOKEN", "")
    if token:
        client = FootballDataOrgClient(token)
        df = client.fetch_multiple_leagues(codes)
    else:
        df = pd.DataFrame()

    if df.empty:
        cached = store.load_matches("football_fdo")
        if not cached.empty:
            logger.warning("football-data.org token missing; reusing cached football_fdo parquet.")
            df = cached

    if df.empty:
        logger.warning("No data from football-data.org — use --source mock or set FOOTBALL_DATA_ORG_TOKEN")
        return 0

    df = _apply_date_window(df, start, end)
    df = _drop_real_odds_columns(df)
    if rate_limit_delay:
        logger.info("Requested rate-limit delay: %.1fs (client enforces 6.0s minimum)", rate_limit_delay)
    store.save_matches(df, source="football_fdo")
    return len(df)


def ingest_football_data_co_uk(store: LocalDataStore, leagues: str, seasons: str) -> int:
    """Ingest historical odds with Pinnacle closing lines from football-data.co.uk."""
    league_list = [c.strip() for c in leagues.split(",")]
    season_list = [s.strip() for s in seasons.split(",")] if seasons else None
    client = FootballDataCoUkClient(cache_dir=str(store.root / "cache" / "fdcouk"))
    df = client.fetch_multiple_seasons(leagues=league_list, seasons=season_list)
    if df.empty:
        logger.warning("No data from football-data.co.uk — check connectivity")
        return 0
    store.save_matches(df, source="football_real_odds")
    logger.info("Saved %d matches with real Pinnacle odds to football_real_odds", len(df))
    return len(df)


def ingest_nba_placeholder(store: LocalDataStore) -> int:
    """NBA: use scripts/ingest_nba_data.py when Postgres is up; else document path."""
    logger.info(
        "NBA ingest: run 'poetry run python scripts/ingest_nba_data.py' "
        "(nba_api is free). Local store ready at %s", store.root
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest free betting data sources")
    parser.add_argument("--sport", choices=["football", "nba", "ufc"], default="football")
    parser.add_argument(
        "--source",
        choices=["mock", "football-data", "football-data-co-uk", "parquet"],
        default="mock",
        help="football-data = football-data.org (no odds); football-data-co-uk = real Pinnacle odds",
    )
    parser.add_argument("--start", help="Inclusive start date (YYYY-MM-DD) for football-data source")
    parser.add_argument("--end", help="Inclusive end date (YYYY-MM-DD) for football-data source")
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=6.0,
        help="Requested delay between API calls for football-data.org (minimum 6.0s enforced)",
    )
    parser.add_argument("--leagues", default="PL,PD,SA,BL1,FL1")
    parser.add_argument("--seasons", default="1920,2021,2122,2223,2324",
                        help="Seasons to fetch (football-data-co-uk only), e.g. 2223,2324")
    parser.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))
    args = parser.parse_args()

    store = LocalDataStore(args.data_dir)
    count = 0

    if args.sport == "football":
        if args.source == "mock":
            count = ingest_football_mock(store)
        elif args.source == "football-data":
            count = ingest_football_data_org(
                store,
                args.leagues,
                start=args.start,
                end=args.end,
                rate_limit_delay=args.rate_limit_delay,
            )
        elif args.source == "football-data-co-uk":
            count = ingest_football_data_co_uk(store, args.leagues, args.seasons)
        else:
            df = store.load_matches("football_mock")
            count = len(df)
            logger.info("Loaded existing parquet: %s rows", count)
    elif args.sport == "nba":
        count = ingest_nba_placeholder(store)
    else:
        logger.info("UFC: run ufc_scraper via daily pipeline or manual scrape to data/bronze/")

    logger.info("Done. Rows ingested: %s | Data root: %s", count, store.root.resolve())


if __name__ == "__main__":
    main()
