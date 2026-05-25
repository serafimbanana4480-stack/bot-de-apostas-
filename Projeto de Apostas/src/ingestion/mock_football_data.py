"""
Realistic mock football data with OPEN vs CLOSING odds (CLV + sharp money backtests).
"""
from __future__ import annotations

import datetime
import os
import random
from typing import Optional

import numpy as np
import pandas as pd


def _true_probs_from_lambda(lh: float, la: float, n: int = 8000) -> tuple[float, float, float]:
    g1 = np.random.poisson(lh, n)
    g2 = np.random.poisson(la, n)
    p1 = (g1 > g2).mean()
    p2 = (g1 < g2).mean()
    px = 1.0 - p1 - p2
    return float(p1), float(max(0.05, px)), float(p2)


def _apply_vig(p1: float, px: float, p2: float, vig: float = 1.03) -> tuple[float, float, float]:
    total = p1 + px + p2
    return (
        round(1.0 / (p1 / total * vig), 2),
        round(1.0 / (px / total * vig), 2),
        round(1.0 / (p2 / total * vig), 2),
    )


def generate_mock_football_data(
    num_seasons: int = 5,
    teams_per_league: int = 20,
    seed: Optional[int] = 42,
) -> pd.DataFrame:
    """
    Generates matches with:
    - open_odd_* : odds 24-72h before kickoff (what we can bet on)
    - odd_* / pin_close_* : Pinnacle-style closing line (efficient)
    - line_movement_home : % change open -> close on home side
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    teams = [f"Team_{chr(65 + i)}{i}" for i in range(teams_per_league)]
    true_strengths = {t: np.random.normal(1.2, 0.4) for t in teams}
    home_adv = 0.3
    matches = []
    start_date = datetime.date(2019, 8, 1)
    match_id = 1

    for season in range(num_seasons):
        season_start = start_date.replace(year=start_date.year + season)
        for home_team in teams:
            for away_team in teams:
                if home_team == away_team:
                    continue

                lh = max(0.1, true_strengths[home_team] + home_adv - true_strengths[away_team] * 0.5)
                la = max(0.1, true_strengths[away_team] - true_strengths[home_team] * 0.5)
                home_goals = int(np.random.poisson(lh))
                away_goals = int(np.random.poisson(la))

                if home_goals > away_goals:
                    outcome = "1"
                elif home_goals == away_goals:
                    outcome = "X"
                else:
                    outcome = "2"

                p1, px, p2 = _true_probs_from_lambda(lh, la)
                # Closing: efficient market (small noise)
                close_p1 = max(0.05, p1 + np.random.normal(0, 0.02))
                close_px = max(0.05, px + np.random.normal(0, 0.02))
                close_p2 = max(0.05, p2 + np.random.normal(0, 0.02))
                pin_1, pin_x, pin_2 = _apply_vig(close_p1, close_px, close_p2, vig=1.02)

                # Opening: softer line (more noise + occasional mispricing for edge)
                open_p1 = max(0.05, close_p1 + np.random.normal(0, 0.06))
                open_px = max(0.05, close_px + np.random.normal(0, 0.04))
                open_p2 = max(0.05, close_p2 + np.random.normal(0, 0.06))
                open_1, open_x, open_2 = _apply_vig(open_p1, open_px, open_p2, vig=1.04)

                # Simulate sharp steam: 35% of games shorten home line into close
                if np.random.random() < 0.35 and outcome == "1":
                    open_1 = round(pin_1 * np.random.uniform(1.04, 1.12), 2)
                # Simulate drift against home: 25% games home odd rises (bad for home backers)
                elif np.random.random() < 0.25:
                    open_1 = round(pin_1 * np.random.uniform(0.88, 0.96), 2)

                line_move_home = (pin_1 / open_1) - 1.0 if open_1 > 0 else 0.0

                match_date = season_start + datetime.timedelta(days=random.randint(0, 280))
                matches.append({
                    "match_id": match_id,
                    "date": match_date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "actual_outcome": outcome,
                    "league": "MOCK_PL",
                    "open_odd_home": open_1,
                    "open_odd_draw": open_x,
                    "open_odd_away": open_2,
                    "odd_1": pin_1,
                    "odd_X": pin_x,
                    "odd_2": pin_2,
                    "pin_close_home": pin_1,
                    "pin_close_draw": pin_x,
                    "pin_close_away": pin_2,
                    "line_movement_home": round(line_move_home, 4),
                    "closing_odd": pin_1 if outcome == "1" else (pin_x if outcome == "X" else pin_2),
                })
                match_id += 1

    df = pd.DataFrame(matches)
    return df.sort_values("date").reset_index(drop=True)


def ensure_mock_dataset(data_dir: str = "data", force: bool = False) -> pd.DataFrame:
    """Load or regenerate mock CSV with open/close columns."""
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "mock_football.csv")
    if not force and os.path.exists(path):
        df = pd.read_csv(path)
        if "open_odd_home" in df.columns and "pin_close_home" in df.columns:
            return df
    df = generate_mock_football_data(num_seasons=5, seed=42)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    data_dir = os.getenv("DATA_DIR", "data")
    df = ensure_mock_dataset(data_dir, force=True)
    print(f"Generated {len(df)} matches with open/close odds → {data_dir}/mock_football.csv")
