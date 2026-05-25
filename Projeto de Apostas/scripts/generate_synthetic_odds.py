#!/usr/bin/env python3
"""
Generate realistic synthetic odds for historical matches using Poisson probabilities.

This allows backtesting on real match data from football-data.org (which does not 
provide historical odds in the free tier).

Usage:
    py scripts/generate_synthetic_odds.py
    py scripts/generate_synthetic_odds.py --margin 0.08 --seed 42

Theory:
    1. Fit Poisson model to all historical matches
    2. For each match, predict home/draw/away probabilities
    3. Convert to fair odds: odd_fair = 1 / prob
    4. Apply bookmaker margin (overround): odd_market = odd_fair / (1 + margin)
    5. Add small random noise per match to simulate different bookmakers
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.local_store import LocalDataStore
from src.ml.models.football_poisson import FootballPoissonModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("synthetic_odds")


def generate_synthetic_odds(
    data_dir: str = "data",
    margin: float = 0.07,
    noise_std: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic odds for all matches in football_fdo.

    Args:
        margin: Bookmaker overround (e.g., 0.07 = 7% margin)
        noise_std: Standard deviation of multiplicative noise per match
        seed: Random seed for reproducibility
    """
    store = LocalDataStore(data_dir)
    df = store.load_matches("football_fdo")
    if df.empty:
        raise FileNotFoundError(
            "No real football data. Run: scripts/ingest_free_data.py --source football-data"
        )

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Fit Poisson model on all data
    logger.info("Fitting Poisson model to %d matches...", len(df))
    model = FootballPoissonModel(use_dixon_coles=True)
    model.fit(df, calibrate=False)  # No calibration needed for synthetic odds

    rng = np.random.RandomState(seed)

    logger.info("Generating synthetic odds with %.1f%% margin...", margin * 100)
    odds_home, odds_draw, odds_away = [], [], []

    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"], row["away_team"],
            league=row.get("league"),
            apply_calibration=False,
        )
        p1, pX, p2 = probs["1"], probs["X"], probs["2"]

        # Convert to fair odds
        fair_home = 1.0 / p1
        fair_draw = 1.0 / pX
        fair_away = 1.0 / p2

        # Apply bookmaker margin (distribute proportionally to probability)
        # Higher prob -> lower odd reduction (favorites pay less margin)
        margin_home = margin * (p1 / (p1 + pX + p2))
        margin_draw = margin * (pX / (p1 + pX + p2))
        margin_away = margin * (p2 / (p1 + pX + p2))

        # Add random noise per match
        noise_h = rng.lognormal(0, noise_std)
        noise_d = rng.lognormal(0, noise_std)
        noise_a = rng.lognormal(0, noise_std)

        odd_h = fair_home / (1 + margin_home) * noise_h
        odd_d = fair_draw / (1 + margin_draw) * noise_d
        odd_a = fair_away / (1 + margin_away) * noise_a

        odds_home.append(round(odd_h, 2))
        odds_draw.append(round(odd_d, 2))
        odds_away.append(round(odd_a, 2))

    df["odd_1"] = odds_home
    df["odd_X"] = odds_draw
    df["odd_2"] = odds_away

    # For CLV, create synthetic closing odds (slightly different from open)
    df["open_odd_home"] = df["odd_1"]
    df["pin_close_home"] = df["odd_1"] * rng.uniform(0.95, 1.05, size=len(df))
    df["pin_close_draw"] = df["odd_X"] * rng.uniform(0.95, 1.05, size=len(df))
    df["pin_close_away"] = df["odd_2"] * rng.uniform(0.95, 1.05, size=len(df))

    # Save back to football_fdo
    store.save_matches(df, "football_fdo")
    logger.info("Saved %d matches with synthetic odds", len(df))

    # Stats
    logger.info("Odds stats:")
    logger.info("  Home: mean=%.2f, median=%.2f", df["odd_1"].mean(), df["odd_1"].median())
    logger.info("  Draw: mean=%.2f, median=%.2f", df["odd_X"].mean(), df["odd_X"].median())
    logger.info("  Away: mean=%.2f, median=%.2f", df["odd_2"].mean(), df["odd_2"].median())

    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic odds for historical matches")
    parser.add_argument("--margin", type=float, default=0.07, help="Bookmaker margin (default: 0.07)")
    parser.add_argument("--noise", type=float, default=0.05, help="Odds noise std (default: 0.05)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()

    generate_synthetic_odds(
        data_dir=args.data_dir,
        margin=args.margin,
        noise_std=args.noise,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
