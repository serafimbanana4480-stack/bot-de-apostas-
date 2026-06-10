#!/usr/bin/env python3
"""
Unified ZERO-COST training CLI for the betting bot.

Usage:
  poetry run python scripts/train_bot.py football --source football-data-co-uk --calibrate
  poetry run python scripts/train_bot.py football --source football-data-co-uk --walk-forward
  poetry run python scripts/train_bot.py football --walk-forward
  poetry run python scripts/train_bot.py report --clv
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.local_store import LocalDataStore
from src.ml.models.football_poisson import FootballPoissonModel
from src.validation.leakage_detector import LeakageDetector
from src.validation.walk_forward import WalkForwardValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_bot")


def load_football_df(store: LocalDataStore, source: str) -> pd.DataFrame:
    source = source.replace("_", "-")
    if source == "football-data":
        # Real match results from football-data.org (no odds in free tier)
        df = store.load_matches("football_fdo")
        if df.empty:
            raise FileNotFoundError(
                "No football-data.org parquet. Run: "
                "scripts/ingest_free_data.py --source football-data"
            )
    elif source in {"mock", "backtest"}:
        raise ValueError(
            "MOCK DATA IS NOT ALLOWED. Use 'football-data-co-uk' for real historical odds. "
            "Run: scripts/ingest_free_data.py --source football-data-co-uk --sport football"
        )
    elif source in {"football-real-odds", "football-data-co-uk", "real-odds", "real"}:
        # Real Pinnacle open/close odds from football-data.co.uk.
        df = store.load_matches("football_real_odds")
        if df.empty:
            raise FileNotFoundError(
                "No real-odds parquet. Run: "
                "scripts/ingest_free_data.py --source football-data-co-uk --sport football"
            )
    else:
        raise ValueError(
            "Unknown source: "
            f"{source}. Use 'football-data' or 'football-data-co-uk' (recommended)."
        )
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def train_football_poisson(
    df: pd.DataFrame,
    calibrate: bool = True,
    walk_forward: bool = False,
) -> dict[str, Any]:
    detector = LeakageDetector()
    check = detector.validate_training_frame(df, time_col="date", target_col="actual_outcome")
    if not check["passed"]:
        logger.warning("Leakage check issues: %s", check)

    if not walk_forward:
        split = int(len(df) * 0.75)
        train_df, test_df = df.iloc[:split], df.iloc[split:]
        model = FootballPoissonModel(use_dixon_coles=True)
        model.fit(train_df, calibrate=calibrate)
        metrics = _evaluate_split(model, test_df)
        return {"mode": "holdout", "metrics": metrics, "leakage": check}

    # Auto-adjust window sizes based on data span for real datasets
    data_span_days = (df["date"].max() - df["date"].min()).days
    if data_span_days < 120:
        # Very short real-data slices (e.g. Jan-Feb 2024) need tighter folds
        train_days, test_days = 30, 7
    elif data_span_days < 500:
        # Real data (~10 months): smaller windows
        train_days, test_days = 120, 30
    else:
        train_days, test_days = 365, 90
    validator = WalkForwardValidator(train_window_days=train_days, test_window_days=test_days)

    def fit_fn(train: pd.DataFrame) -> FootballPoissonModel:
        m = FootballPoissonModel(use_dixon_coles=True)
        m.fit(train, calibrate=calibrate)
        return m

    def predict_fn(model: FootballPoissonModel, test: pd.DataFrame) -> pd.DataFrame:
        out = test.copy()
        probs = []
        for _, row in test.iterrows():
            market_odds = None
            if {"open_odd_home", "open_odd_draw", "open_odd_away"}.issubset(test.columns):
                market_odds = {
                    "1": row.get("open_odd_home"),
                    "X": row.get("open_odd_draw"),
                    "2": row.get("open_odd_away"),
                }
            p = model.predict_match_outcome(
                row["home_team"], row["away_team"],
                league=row.get("league"),
                apply_calibration=calibrate,
                market_odds=market_odds,
            )
            probs.append(p)
        out["prob_1"] = [p["1"] for p in probs]
        return out

    def eval_fn(preds: pd.DataFrame) -> dict[str, float]:
        return _backtest_metrics(preds)

    result = validator.run_backtest(df, "date", fit_fn, predict_fn, eval_fn)
    result["leakage"] = check
    return result


def _evaluate_split(model: FootballPoissonModel, test_df: pd.DataFrame) -> dict[str, float]:
    preds = test_df.copy()
    probs = []
    for _, row in test_df.iterrows():
        market_odds = None
        if {"open_odd_home", "open_odd_draw", "open_odd_away"}.issubset(test_df.columns):
            market_odds = {
                "1": row.get("open_odd_home"),
                "X": row.get("open_odd_draw"),
                "2": row.get("open_odd_away"),
            }
        probs.append(
            model.predict_match_outcome(
                row["home_team"],
                row["away_team"],
                market_odds=market_odds,
            )
        )
    preds["prob_1"] = [p["1"] for p in probs]
    return _backtest_metrics(preds)


def _backtest_metrics(preds: pd.DataFrame) -> dict[str, float]:
    """ROI + extended metrics on home bets when odd_1 exists."""
    if "odd_1" not in preds.columns:
        return {"roi": 0.0, "bets": 0}
    bankroll, bets, wins = 1000.0, 0, 0
    returns = []
    for _, row in preds.iterrows():
        edge = row.get("prob_1", 0) - (1.0 / row["odd_1"]) if row["odd_1"] else 0
        if edge < 0.03:
            continue
        stake = min(bankroll * 0.02, 20.0)
        bets += 1
        won = row.get("actual_outcome") == "1" or (
            row.get("home_goals", 0) > row.get("away_goals", 0)
        )
        pnl = stake * (row["odd_1"] - 1) if won else -stake
        bankroll += pnl
        returns.append(pnl / 1000.0)
        if won:
            wins += 1
    roi = (bankroll - 1000.0) / 1000.0
    ret = np.array(returns) if returns else np.array([0.0])
    downside = ret[ret < 0]
    sortino = (
        float(ret.mean() / (downside.std() + 1e-9) * np.sqrt(252))
        if len(downside) else 0.0
    )
    peak, max_dd = 1000.0, 0.0
    eq = 1000.0
    for r in returns:
        eq += r * 1000.0
        peak = max(peak, eq)
        max_dd = max(max_dd, (peak - eq) / peak)
    calmar = roi / max_dd if max_dd > 1e-6 else 0.0
    gross_profit = sum(r for r in returns if r > 0)
    gross_loss = abs(sum(r for r in returns if r < 0)) or 1e-9
    return {
        "roi": round(roi, 4),
        "bets": bets,
        "win_rate": round(wins / bets, 4) if bets else 0.0,
        "sortino": round(sortino, 4),
        "calmar": round(calmar, 4),
        "max_drawdown": round(max_dd, 4),
        "profit_factor": round(gross_profit / gross_loss, 4),
        "final_bankroll": round(bankroll, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train betting bot (zero-cost mode)")
    sub = parser.add_subparsers(dest="command")

    fb = sub.add_parser("football", help="Train football Poisson model")
    fb.add_argument(
        "--source",
        default="mock",
        choices=[
            "football-data",
            "football_real_odds",
            "football-real-odds",
            "real-odds",
            "mock",
            "backtest",
        ],
    )
    fb.add_argument("--calibrate", action="store_true", default=True)
    fb.add_argument("--walk-forward", action="store_true")
    fb.add_argument(
        "--objective",
        default="logloss",
        choices=["logloss", "clv", "clv-asymmetric"],
        help="Training objective: logloss, clv, or clv-asymmetric "
        "(penalizes false positives more)",
    )
    fb.add_argument(
        "--multi-objective",
        action="store_true",
        help="Use Optuna multi-objective optimization (Pareto front: ROI, Sharpe, drawdown)",
    )
    fb.add_argument(
        "--nested-cv",
        action="store_true",
        help="Use nested cross-validation with inner hyperparameter optimization",
    )
    fb.add_argument(
        "--n-trials",
        type=int,
        default=50,
        help="Number of Optuna trials (for --multi-objective or --nested-cv)",
    )
    fb.add_argument(
        "--bootstrap",
        action="store_true",
        help="Run bootstrap backtest for confidence intervals after training",
    )
    fb.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))

    rep = sub.add_parser("report", help="Generate reports")
    rep.add_argument("--clv", action="store_true", help="Run CLV report script")
    rep.add_argument("--data-dir", default=os.getenv("DATA_DIR", "data"))

    args = parser.parse_args()
    store = LocalDataStore(getattr(args, "data_dir", "data"))

    if args.command == "football":
        df = load_football_df(store, args.source)
        logger.info("Training on %s matches (source=%s, objective=%s)", len(df), args.source, args.objective)

        if args.multi_objective:
            # Multi-objective optimization with Pareto front
            from src.ml.training.multi_objective import MultiObjectiveOptimizer, SelectionStrategy
            logger.info("Running multi-objective optimization (%d trials)...", args.n_trials)

            # Prepare data for XGBoost
            split = int(len(df) * 0.75)
            train_df, val_df = df.iloc[:split], df.iloc[split:]
            feature_cols = [c for c in train_df.columns if c not in {"date", "actual_outcome", "game_date"}]

            X_train = train_df[feature_cols].select_dtypes(include=[np.number]).values
            # Encode string outcomes ('1','X','2') to binary: home win = 1, else 0
            y_raw = train_df["actual_outcome"].values if "actual_outcome" in train_df else np.ones(len(train_df))
            y_train = np.array([1.0 if str(v) == "1" else 0.0 for v in y_raw], dtype=np.float64)
            odds_train = train_df["odd_1"].values if "odd_1" in train_df else np.ones(len(train_df)) * 2.0
            X_val = val_df[feature_cols].select_dtypes(include=[np.number]).values
            y_raw_val = val_df["actual_outcome"].values if "actual_outcome" in val_df else np.ones(len(val_df))
            y_val = np.array([1.0 if str(v) == "1" else 0.0 for v in y_raw_val], dtype=np.float64)
            odds_val = val_df["odd_1"].values if "odd_1" in val_df else np.ones(len(val_df)) * 2.0

            optimizer = MultiObjectiveOptimizer(
                X_train, y_train, odds_train,
                X_val, y_val, odds_val,
                n_trials=args.n_trials,
                objective="clv" if args.objective != "logloss" else "logloss",
            )
            study = optimizer.optimize()
            best = optimizer.select_model(strategy=SelectionStrategy.MAX_SHARPE_DD_LT_15)
            model = optimizer.train_final(best.params)
            pareto_df = optimizer.get_pareto_dataframe()

            result = {
                "mode": "multi_objective",
                "pareto_front_size": len(pareto_df),
                "selected_params": best.params,
                "selected_metrics": {
                    "roi": -best.values[0],
                    "sharpe": -best.values[1],
                    "max_drawdown": best.values[2],
                },
                "objective": args.objective,
            }
            logger.info("Multi-objective result: %s", result)

        elif args.nested_cv:
            # Nested cross-validation with inner hyperparameter optimization
            from src.ml.training.nested_cv import NestedWalkForwardCV
            logger.info("Running nested CV (%d outer folds, %d Optuna trials)...", 5, args.n_trials)

            feature_cols = [c for c in df.columns if c not in {"date", "actual_outcome", "game_date"}]
            X = df[feature_cols].select_dtypes(include=[np.number])
            X["game_date"] = df["date"]
            y_raw = df["actual_outcome"].values if "actual_outcome" in df else np.ones(len(df))
            y = np.array([1.0 if str(v) == "1" else 0.0 for v in y_raw], dtype=np.float64)
            odds = df["odd_1"].values if "odd_1" in df else np.ones(len(df)) * 2.0

            nested = NestedWalkForwardCV(
                n_outer=5,
                n_inner=3,
                optimizer="bayesian",
                n_trials=args.n_trials,
                objective="clv" if args.objective != "logloss" else "logloss",
            )
            result = nested.fit(X, y, odds, date_col="game_date")
            result["mode"] = "nested_cv"
            result["objective"] = args.objective
            logger.info("Nested CV result: overall_metrics=%s", result.get("overall_metrics"))

        else:
            result = train_football_poisson(
                df, calibrate=args.calibrate, walk_forward=args.walk_forward,
            )
            result["objective"] = args.objective

        # Bootstrap backtest for confidence intervals
        if args.bootstrap and "bets" in result or args.bootstrap and args.walk_forward:
            try:
                from src.simulation.bootstrap_backtest import BootstrapBacktest
                bt = BootstrapBacktest(n_bootstrap=1000, method="block", block_size=5)
                # If we have a bets dataframe, bootstrap it
                if "combined_predictions" in result and isinstance(result["combined_predictions"], pd.DataFrame):
                    bt_result = bt.run(result["combined_predictions"], pnl_col="pnl_units" if "pnl_units" in result["combined_predictions"].columns else "roi")
                    result["bootstrap"] = bt_result
                    logger.info("Bootstrap CI 95%% ROI: %s", bt_result.get("ci_95", {}).get("roi"))
            except Exception as e:
                logger.warning("Bootstrap backtest failed: %s", e)

        store.save_report(result, "last_football_train")
        logger.info("Result: %s", result)
    elif args.command == "report" and args.clv:
        os.system(f'{sys.executable} {os.path.join(os.path.dirname(__file__), "run_clv_report.py")}')
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
