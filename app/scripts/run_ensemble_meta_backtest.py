#!/usr/bin/env python3
"""
Ensemble + Meta-Labeling Integrated Backtest

Combina FootballEnsemble (Poisson + XGBoost + Logistic Regression + meta-learner)
com MetaLabeler (market features) para filtrar sinais de baixa qualidade.

Pipeline:
  1. Load matches_football_real_odds.parquet
  2. Temporal split: 60% train / 20% val / 20% test
  3. Fit FootballEnsemble on train
  4. Generate OOS signals on val  -> train MetaLabeler
  5. Generate OOS signals on test -> evaluate WITH vs WITHOUT meta-labeling
  6. Compare against baseline Poisson-only model

Usage:
    py -3 scripts/run_ensemble_meta_backtest.py
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.meta_labeling import MetaLabeler, evaluate_meta_labeling
from src.ml.ensemble.football_ensemble import FootballEnsemble
from src.ml.models.football_poisson import FootballPoissonModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("ensemble_meta_backtest")


def load_data(parquet_path: Path) -> pd.DataFrame:
    """Load and clean real odds data."""
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    core = [
        "home_team", "away_team", "home_goals", "away_goals",
        "actual_outcome", "open_odd_home", "pin_close_home",
    ]
    before = len(df)
    df = df.dropna(subset=core)
    after = len(df)
    if before != after:
        logger.warning("Dropped %d rows with missing core columns", before - after)
    return df.sort_values("date").reset_index(drop=True)


def generate_ensemble_signals(
    model: FootballEnsemble,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Run ensemble model on DataFrame and return signal records."""
    records = []
    for _, row in df.iterrows():
        probs = model.predict(
            row["home_team"],
            row["away_team"],
            league=row.get("league"),
            odd_1=row.get("odd_1", 2.0),
            odd_X=row.get("odd_X", 3.0),
            odd_2=row.get("odd_2", 3.0),
            open_odd_home=row.get("open_odd_home"),
            open_odd_away=row.get("open_odd_away"),
            open_odd_draw=row.get("open_odd_draw"),
            date=row.get("date"),
        )
        pred_outcome = max(
            ("1", "X", "2"), key=lambda k: probs.get(k, 0)
        )
        records.append({
            "predicted_outcome": pred_outcome,
            "prob_home": probs["1"],
            "prob_draw": probs["X"],
            "prob_away": probs["2"],
            "actual_outcome": row["actual_outcome"],
        })
    return pd.DataFrame(records)


def generate_poisson_signals(
    model: FootballPoissonModel,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Run Poisson model on DataFrame and return signal records."""
    records = []
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"],
            row["away_team"],
            league=row.get("league"),
            apply_calibration=model.is_calibrated,
            market_odds={"1": row.get("odd_1"), "X": row.get("odd_X"), "2": row.get("odd_2")},
        )
        pred_outcome = max(
            ("1", "X", "2"), key=lambda k: probs.get(k, 0)
        )
        records.append({
            "predicted_outcome": pred_outcome,
            "prob_home": probs["1"],
            "prob_draw": probs["X"],
            "prob_away": probs["2"],
            "actual_outcome": row["actual_outcome"],
        })
    return pd.DataFrame(records)


def backtest_signals(
    signals: pd.DataFrame,
    df_odds: pd.DataFrame,
    stake: float = 1.0,
) -> dict:
    """Simple backtest: flat stake on predicted outcome."""
    correct = signals["predicted_outcome"] == signals["actual_outcome"]
    odd_map = {"1": "odd_1", "X": "odd_X", "2": "odd_2"}

    # Align indices — both should be 0..N-1
    signals = signals.reset_index(drop=True)
    df_odds = df_odds.reset_index(drop=True)

    odds_taken = pd.Series(index=signals.index, dtype=float)
    for outcome, col in odd_map.items():
        mask = signals["predicted_outcome"] == outcome
        if col in df_odds.columns:
            odds_taken[mask] = df_odds.loc[mask, col]
        else:
            odds_taken[mask] = 2.0

    n = len(signals)
    acc = float(correct.mean())
    profit = float((correct * (odds_taken - 1.0) - (~correct) * 1.0).sum())
    roi = profit / (n * stake) if n > 0 else 0.0
    return {
        "n_bets": n,
        "accuracy": round(acc, 4),
        "roi": round(roi, 4),
        "profit": round(profit, 2),
        "avg_odds": round(odds_taken.mean(), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensemble + Meta-Labeling Backtest")
    parser.add_argument("--save-dir", type=str, default="models/ensemble_meta")
    args = parser.parse_args()

    data_path = PROJECT_ROOT / "data" / "bronze" / "matches_football_real_odds.parquet"
    if not data_path.exists():
        logger.error("Data file not found: %s", data_path)
        sys.exit(1)

    df = load_data(data_path)
    logger.info("Loaded %d matches", len(df))

    # Temporal split
    n = len(df)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    logger.info("Splits -> train=%d  val=%d  test=%d", len(df_train), len(df_val), len(df_test))

    # ------------------------------------------------------------------
    # 1. Fit models on train
    # ------------------------------------------------------------------
    logger.info("Fitting FootballEnsemble on train...")
    ensemble = FootballEnsemble(meta_learner="logistic")
    ensemble.fit(df_train, target_col="actual_outcome")

    logger.info("Fitting baseline Poisson on train...")
    poisson = FootballPoissonModel(use_dixon_coles=True, use_context=True)
    poisson.fit(df_train, calibrate=True)

    # ------------------------------------------------------------------
    # 2. Generate OOS signals on validation set -> train MetaLabeler
    # ------------------------------------------------------------------
    logger.info("Generating ensemble signals on validation set...")
    signals_val = generate_ensemble_signals(ensemble, df_val)

    meta_labeler = MetaLabeler(calibrate=True)
    summary = meta_labeler.fit(signals_val, df_val, n_splits=3)
    logger.info("MetaLabeler trained: %s", summary)

    # ------------------------------------------------------------------
    # 3. Generate OOS signals on test set -> evaluate
    # ------------------------------------------------------------------
    logger.info("Generating ensemble signals on test set...")
    signals_test = generate_ensemble_signals(ensemble, df_test)

    logger.info("Generating Poisson signals on test set (baseline)...")
    poisson_signals_test = generate_poisson_signals(poisson, df_test)

    # Backtest: Poisson baseline
    poisson_metrics = backtest_signals(poisson_signals_test, df_test)

    # Backtest: Ensemble without meta-labeling
    ensemble_metrics = backtest_signals(signals_test, df_test)

    # Backtest: Ensemble WITH meta-labeling at different thresholds
    meta_results = []
    for thr in [0.50, 0.55, 0.60, 0.65, 0.70]:
        m = evaluate_meta_labeling(signals_test, df_test, meta_labeler, threshold=thr)
        meta_results.append({
            "threshold": thr,
            **m,
        })
        logger.info(
            "Threshold %.2f | WITHOUT: n=%d acc=%.3f roi=%.3f | WITH: n=%d acc=%.3f roi=%.3f | "
            "Lift acc=%+.3f roi=%+.3f",
            thr,
            m["without_meta_labeling"]["n_bets"],
            m["without_meta_labeling"]["accuracy"],
            m["without_meta_labeling"]["roi"],
            m["with_meta_labeling"]["n_bets"],
            m["with_meta_labeling"]["accuracy"],
            m["with_meta_labeling"]["roi"],
            m["accuracy_lift"],
            m["roi_lift"],
        )

    # ------------------------------------------------------------------
    # 4. Save artifacts
    # ------------------------------------------------------------------
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    ensemble.save(str(save_dir / "ensemble"))
    meta_labeler.save(str(save_dir / "meta_labeler"))
    poisson.save(str(save_dir / "poisson.json"))

    report = {
        "poisson_baseline": poisson_metrics,
        "ensemble_without_meta": ensemble_metrics,
        "ensemble_with_meta": meta_results,
    }
    report_path = save_dir / "backtest_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Artifacts saved to %s", save_dir)

    # ------------------------------------------------------------------
    # 5. Print summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ENSEMBLE + META-LABELING BACKTEST SUMMARY (Test Set)")
    print("=" * 70)
    print(f"{'Model':<35} {'Bets':>6} {'Acc%':>7} {'ROI%':>8} {'Profit':>8}")
    print("-" * 70)
    print(
        f"{'Poisson baseline':<35} {poisson_metrics['n_bets']:>6} "
        f"{poisson_metrics['accuracy']*100:>6.2f}% {poisson_metrics['roi']*100:>7.2f}% "
        f"{poisson_metrics['profit']:>8.2f}"
    )
    print(
        f"{'Ensemble (no filter)':<35} {ensemble_metrics['n_bets']:>6} "
        f"{ensemble_metrics['accuracy']*100:>6.2f}% {ensemble_metrics['roi']*100:>7.2f}% "
        f"{ensemble_metrics['profit']:>8.2f}"
    )
    for r in meta_results:
        m = r["with_meta_labeling"]
        print(
            f"{'Ensemble + Meta (thr=' + str(r['threshold']) + ')':<35} "
            f"{m['n_bets']:>6} {m['accuracy']*100:>6.2f}% {m['roi']*100:>7.2f}% "
            f"{m['profit']:>8.2f}"
        )
    print("=" * 70)

    # Best threshold
    best = max(meta_results, key=lambda x: x["with_meta_labeling"]["roi"])
    print(f"\nBest meta-label threshold: {best['threshold']}")
    print(f"  Accuracy lift: {best['accuracy_lift']:+.3f}")
    print(f"  ROI lift:      {best['roi_lift']:+.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
