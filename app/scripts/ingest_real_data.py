#!/usr/bin/env python3
"""
Ingest real historical football data from free sources.

Usage:
    py scripts/ingest_real_data.py --seasons 2122 2223 2324 --leagues E0 E1 D2 F2 I2
    py scripts/ingest_real_data.py --seasons 2324 --leagues E1 D2 F2 I2 N1 P1

Sources:
    - football-data.co.uk (historical odds with Pinnacle closing)
    - The Odds API (live odds, optional)

NO MOCK DATA IS GENERATED.
If data is unavailable, the script fails explicitly.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.real_data_pipeline import RealDataPipeline, TARGET_LEAGUES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ingest_real_data")


def main():
    parser = argparse.ArgumentParser(description="Ingest real football data")
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=["2122", "2223", "2324"],
        help="Season codes e.g. 2122 2223 2324",
    )
    parser.add_argument(
        "--leagues",
        nargs="+",
        default=["E0", "E1", "D1", "D2", "F1", "F2", "I1", "I2", "N1", "P1"],
        help="League codes e.g. E0 E1 D2 F2 I2 N1 P1",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/bronze/matches_football_real.parquet",
        help="Output parquet path",
    )
    parser.add_argument(
        "--cache",
        type=str,
        default="data/cache/football_data_co_uk",
        help="Cache directory",
    )
    parser.add_argument(
        "--live-odds",
        action="store_true",
        help="Also fetch live odds from The Odds API",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("VBQ-UNIFIED — REAL DATA INGESTION")
    print("=" * 70)
    print(f"Seasons: {args.seasons}")
    print(f"Leagues: {args.leagues}")
    print(f"Target leagues (less efficient = higher priority):")
    for code in args.leagues:
        name = TARGET_LEAGUES.get(code, code)
        print(f"  {code}: {name}")
    print("=" * 70)

    pipeline = RealDataPipeline(
        cache_dir=args.cache,
        output_dir=str(Path(args.output).parent),
    )

    # Build historical dataset
    logger.info("Fetching historical data...")
    df = pipeline.build_training_dataset(
        seasons=args.seasons,
        leagues=args.leagues,
    )

    logger.info("Total matches ingested: %d", len(df))
    logger.info("Date range: %s to %s", df["date"].min().date(), df["date"].max().date())
    logger.info("Leagues: %s", df["league"].unique().tolist())

    # Summary by league
    print("\n--- League Summary ---")
    for league, grp in df.groupby("league"):
        n = len(grp)
        pin_ok = grp["pin_close_home"].notna().sum()
        print(f"  {league}: {n} matches, {pin_ok} with Pinnacle closing odds")

    # Optional: live odds
    if args.live_odds:
        logger.info("Fetching live odds from The Odds API...")
        live = pipeline.fetch_live_odds()
        if not live.empty:
            live_path = Path(args.output).parent / "odds_live.parquet"
            live.to_parquet(live_path, index=False)
            logger.info("Saved %d live odds rows to %s", len(live), live_path)
        else:
            logger.warning("No live odds fetched (check ODDS_API_KEY)")

    print("\n" + "=" * 70)
    print(f"DONE. Real data saved to: {args.output}")
    print(f"Total matches: {len(df)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
