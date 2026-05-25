#!/usr/bin/env python3
"""
Train the real-data MetaLabeler on football odds history.

Pipeline:
  1. Load matches_football_real_odds.parquet
  2. Temporal split: 60% train / 20% val / 20% test
  3. Fit FootballPoissonModel on train
  4. Generate OOS primary signals on val  -> train MetaLabeler
  5. Generate OOS primary signals on test -> evaluate WITH vs WITHOUT meta-labeling
  6. Save model + print backtest metrics

Usage:
    .venv/Scripts/python scripts/train_meta_labeler.py
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.meta_labeling import MetaLabeler, evaluate_meta_labeling
from src.ml.models.football_poisson import FootballPoissonModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("train_meta_labeler")


def load_data(parquet_path: Path) -> pd.DataFrame:
    """Load and clean real odds data."""
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    # Drop rows missing core columns
    core = ["home_team", "away_team", "home_goals", "away_goals",
            "actual_outcome", "open_odd_home", "pin_close_home"]
    before = len(df)
    df = df.dropna(subset=core)
    after = len(df)
    if before != after:
        logger.warning("Dropped %d rows with missing core columns", before - after)
    return df.sort_values("date").reset_index(drop=True)


def generate_primary_signals(
    model: FootballPoissonModel,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Run the Poisson model on a DataFrame and return signal records.

    Each row gets:
        - predicted_outcome: '1', 'X', or '2' (highest probability)
        - prob_home, prob_draw, prob_away
        - actual_outcome (copied from df)
    """
    records = []
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"],
            row["away_team"],
            league=row.get("league"),
            apply_calibration=model.is_calibrated,
            market_odds={"1": row.get("odd_1"), "X": row.get("odd_X"), "2": row.get("odd_2")},
        )
        pred_outcome = max(probs, key=lambda k: probs[k] if k in ("1", "X", "2") else 0)
        records.append({
            "predicted_outcome": pred_outcome,
            "prob_home": probs["1"],
            "prob_draw": probs["X"],
            "prob_away": probs["2"],
            "actual_outcome": row["actual_outcome"],
        })
    return pd.DataFrame(records)


def train_meta_labeler(args: argparse.Namespace) -> None:
    data_path = PROJECT_ROOT / "data" / "bronze" / "matches_football_real_odds.parquet"
    if not data_path.exists():
        logger.error("Data file not found: %s", data_path)
        sys.exit(1)

    df = load_data(data_path)
    logger.info("Loaded %d matches (%.1f seasons)", len(df),
                df["date"].dt.year.nunique())

    # ------------------------------------------------------------------
    # Temporal split: 60 / 20 / 20
    # ------------------------------------------------------------------
    n = len(df)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    logger.info("Splits -> train=%d  val=%d  test=%d", len(df_train), len(df_val), len(df_test))

    # ------------------------------------------------------------------
    # 1. Fit primary model on train
    # ------------------------------------------------------------------
    primary_model = FootballPoissonModel(use_dixon_coles=True, use_context=True)
    primary_model.fit(df_train, calibrate=True)
    logger.info("Primary Poisson model fitted on %d matches", len(df_train))

    # ------------------------------------------------------------------
    # 2. Generate OOS signals on validation set -> train meta-labeler
    # ------------------------------------------------------------------
    logger.info("Generating primary signals on validation set...")
    signals_val = generate_primary_signals(primary_model, df_val)

    meta_labeler = MetaLabeler(calibrate=True)
    summary = meta_labeler.fit(signals_val, df_val, n_splits=3)
    logger.info("MetaLabeler trained: %s", summary)

    # ------------------------------------------------------------------
    # 3. Generate OOS signals on test set -> evaluate
    # ------------------------------------------------------------------
    logger.info("Generating primary signals on test set...")
    signals_test = generate_primary_signals(primary_model, df_test)

    # Evaluate at multiple thresholds
    for thr in [0.50, 0.55, 0.60, 0.65]:
        metrics = evaluate_meta_labeling(signals_test, df_test, meta_labeler, threshold=thr)
        logger.info(
            "Threshold %.2f | WITHOUT: n=%d acc=%.3f roi=%.3f | WITH: n=%d acc=%.3f roi=%.3f | "
            "Lift acc=%+.3f roi=%+.3f",
            thr,
            metrics["without_meta_labeling"]["n_bets"],
            metrics["without_meta_labeling"]["accuracy"],
            metrics["without_meta_labeling"]["roi"],
            metrics["with_meta_labeling"]["n_bets"],
            metrics["with_meta_labeling"]["accuracy"],
            metrics["with_meta_labeling"]["roi"],
            metrics["accuracy_lift"],
            metrics["roi_lift"],
        )

    # ------------------------------------------------------------------
    # 4. Save artifacts
    # ------------------------------------------------------------------
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    meta_path = save_dir / "meta_labeler"
    meta_labeler.save(str(meta_path))

    primary_path = save_dir / "primary_poisson.json"
    primary_model.save(str(primary_path))
    logger.info("Artifacts saved to %s", save_dir)

    # ------------------------------------------------------------------
    # 5. Final summary print
    # ------------------------------------------------------------------
    best_thr = 0.55
    best_metrics = evaluate_meta_labeling(signals_test, df_test, meta_labeler, threshold=best_thr)
    print("\n" + "=" * 60)
    print("META-LABELER BACKTEST SUMMARY (Test Set)")
    print("=" * 60)
    print(f"Primary model accuracy (no filter): {best_metrics['without_meta_labeling']['accuracy']:.3f}")
    print(f"Primary model ROI       (no filter): {best_metrics['without_meta_labeling']['roi']:.3f}")
    print(f"Primary model #bets    (no filter): {best_metrics['without_meta_labeling']['n_bets']}")
    print("-" * 60)
    print(f"Meta-label threshold: {best_thr}")
    print(f"With meta-labeling accuracy: {best_metrics['with_meta_labeling']['accuracy']:.3f}")
    print(f"With meta-labeling ROI:      {best_metrics['with_meta_labeling']['roi']:.3f}")
    print(f"With meta-labeling #bets:    {best_metrics['with_meta_labeling']['n_bets']}")
    print(f"Bets filtered out:           {best_metrics['bets_filtered']}")
    print(f"Accuracy lift:               {best_metrics['accuracy_lift']:+.3f}")
    print(f"ROI lift:                    {best_metrics['roi_lift']:+.3f}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train real-data meta-labeler")
    parser.add_argument("--save-dir", type=str, default="models/meta_labeling")
    args = parser.parse_args()
    train_meta_labeler(args)


if __name__ == "__main__":
    main()
