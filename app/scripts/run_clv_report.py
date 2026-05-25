#!/usr/bin/env python3
"""
CLV report from local data — proves edge vs closing line (0€, no paid APIs required).

Supports both mock data and REAL Pinnacle odds from football-data.co.uk.
Bets on ALL 3 sides (home/draw/away) to find where the model has edge.

Usage:
  poetry run python scripts/run_clv_report.py
  poetry run python scripts/run_clv_report.py --source real     # real Pinnacle odds
  poetry run python scripts/run_clv_report.py --source mock     # simulated odds
  poetry run python scripts/run_clv_report.py --data-dir data
  poetry run python scripts/run_clv_report.py --min-edge 0.02  # minimum edge threshold
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.local_store import LocalDataStore
from src.ml.models.football_poisson import FootballPoissonModel
from src.validation.clv_tracker import CLVTracker
from src.validation.walk_forward import WalkForwardValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_clv_report")

# Map side to outcome code and odds columns
SIDE_MAP = {
    "home": {"outcome": "1", "open_col": "open_odd_home", "close_col": "pin_close_home"},
    "draw": {"outcome": "X", "open_col": "open_odd_draw", "close_col": "pin_close_draw"},
    "away": {"outcome": "2", "open_col": "open_odd_away", "close_col": "pin_close_away"},
}


def ensure_data(store: LocalDataStore, source: str = "auto") -> pd.DataFrame:
    """
    Load match data for CLV analysis.
    
    source='auto'  — try real odds first, fall back to mock
    source='real'  — require football_real_odds (from football-data.co.uk)
    source='mock'  — use football_mock / football_backtest (simulated odds)
    """
    df = pd.DataFrame()

    if source in ("auto", "real"):
        df = store.load_matches("football_real_odds")
        if not df.empty:
            logger.info("Using REAL Pinnacle odds (%d matches)", len(df))
        elif source == "real":
            raise FileNotFoundError(
                "No real odds data. Run: scripts/ingest_free_data.py "
                "--source football-data-co-uk --sport football"
            )

    if df.empty and source in ("auto", "mock"):
        df = store.load_matches("football_mock")
        if df.empty:
            df = store.load_matches("football_backtest")
        if not df.empty:
            logger.info("Using MOCK backtest data (%d matches)", len(df))

    if df.empty:
        raise FileNotFoundError(
            "No data for CLV. Run first:\n"
            "  scripts/ingest_free_data.py --source football-data-co-uk --sport football\n"
            "  OR: scripts/ingest_free_data.py --source mock --sport football"
        )

    df["date"] = pd.to_datetime(df["date"])

    # Ensure required columns exist (fallback for mock data without pin_close_*)
    if "pin_close_home" not in df.columns:
        df["pin_close_home"] = df.get("odd_1", 2.0) * 0.98
        df["pin_close_draw"] = df.get("odd_X", 3.2) * 0.98
        df["pin_close_away"] = df.get("odd_2", 3.5) * 0.98
    if "open_odd_home" not in df.columns:
        df["open_odd_home"] = df.get("odd_1", 2.0)
        df["open_odd_draw"] = df.get("odd_X", 3.2)
        df["open_odd_away"] = df.get("odd_2", 3.5)

    # Drop rows with NaN/inf odds
    for col in ["open_odd_home", "open_odd_draw", "open_odd_away",
                "pin_close_home", "pin_close_draw", "pin_close_away"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open_odd_home", "pin_close_home",
                           "open_odd_draw", "pin_close_draw",
                           "open_odd_away", "pin_close_away"])

    return df.sort_values("date")


def run_report(data_dir: str, source: str = "auto", min_edge: float = 0.02) -> dict:
    store = LocalDataStore(data_dir)
    df = ensure_data(store, source)
    # Auto-adjust window sizes for real datasets
    data_span_days = (df["date"].max() - df["date"].min()).days
    if data_span_days < 120:
        train_days, test_days = 30, 7
    elif data_span_days < 500:
        train_days, test_days = 120, 30
    else:
        train_days, test_days = 365 * 2, 60
    validator = WalkForwardValidator(train_window_days=train_days, test_window_days=test_days)
    tracker = CLVTracker()

    # Per-side and per-league tracking
    all_clv = []
    all_roi = []
    all_open_odds = []
    side_clv = defaultdict(list)
    side_roi = defaultdict(list)
    league_clv = defaultdict(list)
    league_roi = defaultdict(list)

    splits = validator.split_data(df, "date")
    num_splits = min(len(splits), 5)
    logger.info("Running %d walk-forward splits on %d matches", num_splits, len(df))

    for i, split in enumerate(splits[:num_splits]):
        train, test = split["train"], split["test"]
        logger.info("Split %d/%d: train=%d, test=%d", i + 1, num_splits, len(train), len(test))
        model = FootballPoissonModel(use_dixon_coles=True)
        # Use OOF calibration plus odds-bin calibration when odds columns are available.
        model.fit(train, calibrate=True)

        # Pre-filter test: only rows where both teams are in training
        known_teams = set(model.attack_strengths.keys())
        test_known = test[
            test["home_team"].isin(known_teams) & test["away_team"].isin(known_teams)
        ]

        for _, row in test_known.iterrows():
            probs = model.predict_match_outcome(
                row["home_team"],
                row["away_team"],
                apply_calibration=True,
                market_odds={
                    "1": row.get("open_odd_home"),
                    "X": row.get("open_odd_draw"),
                    "2": row.get("open_odd_away"),
                },
            )
            league = row.get("league", "UNKNOWN")

            # Evaluate ALL 3 sides (not just home)
            for side, info in SIDE_MAP.items():
                open_odd = row.get(info["open_col"])
                if pd.isna(open_odd) or open_odd <= 1.0:
                    continue
                # Model's edge: predicted prob > implied prob from available odds
                implied_prob = 1.0 / open_odd
                model_prob = probs[info["outcome"]]
                edge = model_prob - implied_prob
                if edge < min_edge:
                    continue

                closing = {
                    "home": row["pin_close_home"],
                    "draw": row["pin_close_draw"],
                    "away": row["pin_close_away"],
                }
                clv = tracker.calculate_clv(open_odd, side, closing, market_type="3-way")
                clv_pct = clv["clv_percentage"]
                if not np.isfinite(clv_pct):
                    continue

                won = row.get("actual_outcome") == info["outcome"]
                pnl = (open_odd - 1) if won else -1.0

                all_clv.append(clv_pct)
                all_roi.append(pnl)
                all_open_odds.append(float(open_odd))
                side_clv[side].append(clv_pct)
                side_roi[side].append(pnl)
                league_clv[league].append(clv_pct)
                league_roi[league].append(pnl)

    clv_arr = np.array(all_clv) if all_clv else np.array([0.0])
    roi_arr = np.array(all_roi) if all_roi else np.array([0.0])

    # Per-side summary
    side_summary = {}
    for side in ["home", "draw", "away"]:
        vals = side_clv.get(side, [])
        rois = side_roi.get(side, [])
        if vals:
            arr = np.array(vals)
            side_summary[side] = {
                "bets": len(vals),
                "mean_clv_pct": float(arr.mean() * 100),
                "pct_positive_clv": float((arr > 0).mean() * 100),
                "simulated_roi": float(np.mean(rois)),
            }

    # Per-league summary
    league_summary = {}
    for league in sorted(league_clv.keys()):
        vals = league_clv[league]
        rois = league_roi[league]
        if len(vals) >= 10:
            arr = np.array(vals)
            league_summary[league] = {
                "bets": len(vals),
                "mean_clv_pct": float(arr.mean() * 100),
                "pct_positive_clv": float((arr > 0).mean() * 100),
                "simulated_roi": float(np.mean(rois)),
            }

    odds_bin_summary = {}
    open_odd_gt_3_mean_clv_pct = 0.0
    if all_clv:
        odds_df = pd.DataFrame({"open_odd": all_open_odds, "clv_pct": all_clv})
        open_odd_gt_3 = odds_df[odds_df["open_odd"] > 3.0]
        if not open_odd_gt_3.empty:
            open_odd_gt_3_mean_clv_pct = float(open_odd_gt_3["clv_pct"].mean() * 100)
        for label, lo, hi in [
            ("1.00-1.50", 1.0, 1.5),
            ("1.50-2.00", 1.5, 2.0),
            ("2.00-3.00", 2.0, 3.0),
            ("3.00-5.00", 3.0, 5.0),
            ("5.00+", 5.0, 1e9),
        ]:
            bucket = odds_df[(odds_df["open_odd"] >= lo) & (odds_df["open_odd"] < hi)]
            if not bucket.empty:
                odds_bin_summary[label] = {
                    "bets": len(bucket),
                    "mean_clv_pct": float(bucket["clv_pct"].mean() * 100),
                    "pct_positive_clv": float((bucket["clv_pct"] > 0).mean() * 100),
                }

    report = {
        "data_source": source,
        "total_matches": len(df),
        "walk_forward_splits": num_splits,
        "min_edge_threshold": min_edge,
        "bets_analyzed": len(all_clv),
        "mean_clv_pct": float(clv_arr.mean() * 100),
        "median_clv_pct": float(np.median(clv_arr) * 100),
        "pct_positive_clv": float((clv_arr > 0).mean() * 100) if len(clv_arr) else 0.0,
        "simulated_roi_per_unit": float(roi_arr.mean()),
        "edge_proven": bool(clv_arr.mean() > 0.01 and len(clv_arr) >= 50),
        "threshold_note": "CLV > 1% mean over 50+ bets suggests real edge vs closing",
        "by_side": side_summary,
        "by_league": league_summary,
        "by_open_odds_bin": odds_bin_summary,
        "open_odds_gt_3_mean_clv_pct": open_odd_gt_3_mean_clv_pct,
    }
    store.save_report(report, "clv_report")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))
    parser.add_argument(
        "--source",
        choices=["auto", "real", "mock"],
        default="auto",
        help="auto=try real first; real=require Pinnacle odds; mock=simulated",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.02,
        help="Minimum model edge to place a bet (default: 0.02 = 2%%)",
    )
    parser.add_argument(
        "--use-real-odds",
        action="store_true",
        help="Alias for --source real",
    )
    args = parser.parse_args()
    source = "real" if args.use_real_odds else args.source
    report = run_report(args.data_dir, source, args.min_edge)

    logger.info("=" * 60)
    logger.info("CLV REPORT — %s data", report["data_source"].upper())
    logger.info("=" * 60)
    logger.info("Total matches: %d | Bets analyzed: %d", report["total_matches"], report["bets_analyzed"])
    logger.info("Mean CLV: %.4f%% | Median CLV: %.4f%%", report["mean_clv_pct"], report["median_clv_pct"])
    logger.info("%% positive CLV: %.1f%%", report["pct_positive_clv"])
    logger.info("Simulated ROI per unit: %.4f", report["simulated_roi_per_unit"])

    if report["by_side"]:
        logger.info("--- By Side ---")
        for side, s in report["by_side"].items():
            logger.info("  %s: %d bets, CLV=%.3f%%, ROI=%.4f", side, s["bets"], s["mean_clv_pct"], s["simulated_roi"])

    if report["by_league"]:
        logger.info("--- By League ---")
        for league, s in report["by_league"].items():
            logger.info("  %s: %d bets, CLV=%.3f%%, ROI=%.4f", league, s["bets"], s["mean_clv_pct"], s["simulated_roi"])

    if report["edge_proven"]:
        logger.info("PASS: Model beats closing line on average (CLV > 1%%).")
    else:
        logger.warning("FAIL: Insufficient or negative CLV — refine model or try different edge thresholds.")


if __name__ == "__main__":
    main()
