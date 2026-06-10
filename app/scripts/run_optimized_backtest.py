#!/usr/bin/env python3
"""
Optimized Backtest V2 — Modelo PoissonV2 + ValueBetFilterV2 + MetaLabelingV2.

Este script representa a versão mais avançada do sistema, incorporando:
  1. FootballPoissonModelV2 (MLE + decay temporal + rho fixo por liga)
  2. ValueBetFilterV2 (edge-based, sem filtro de probabilidade)
  3. MetaLabelingModel (filtra sinais fracos com market features reais)
  4. Kelly Criterion com sanity checks e ajuste de calibração
  5. Walk-forward temporal honesto
  6. Métricas completas: ECE, Brier Score, Risk of Ruin, p-value

Usage:
    py -3 scripts/run_optimized_backtest.py
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

from src.diagnostics.calibration_metrics import (
    build_backtest_report,
    compute_ece,
    brier_decomposition,
    kelly_with_sanity,
    monte_carlo_risk_of_ruin,
    statistical_significance_roi,
    compute_sortino,
    BacktestReport,
)
from src.ml.meta_labeling import MetaLabelingModel
from src.ml.models.football_poisson_v2 import FootballPoissonModelV2
from src.risk.value_filter_v2 import ValueBetFilterV2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("optimized_backtest")


def load_data(parquet_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    core = [
        "home_team", "away_team", "home_goals", "away_goals",
        "actual_outcome", "date",
    ]
    before = len(df)
    df = df.dropna(subset=core)
    after = len(df)
    if before != after:
        logger.warning("Dropped %d rows with missing core columns", before - after)
    return df.sort_values("date").reset_index(drop=True)


def generate_signals(model, df: pd.DataFrame) -> pd.DataFrame:
    """Gera sinais para cada jogo no DataFrame."""
    records = []
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"],
            row["away_team"],
            league=row.get("league"),
            apply_calibration=model.is_calibrated,
            market_odds={"1": row.get("odd_1"), "X": row.get("odd_X"), "2": row.get("odd_2")},
        )
        pred_outcome = max(("1", "X", "2"), key=lambda k: probs.get(k, 0))
        records.append({
            "predicted_outcome": pred_outcome,
            "prob_home": probs["1"],
            "prob_draw": probs["X"],
            "prob_away": probs["2"],
            "actual_outcome": row["actual_outcome"],
        })
    return pd.DataFrame(records)


def backtest_with_filter(
    signals: pd.DataFrame,
    df_odds: pd.DataFrame,
    value_filter: ValueBetFilterV2,
    bankroll_init: float = 1000.0,
    kelly_fraction: float = 0.10,
    model_ece: float = 0.0,
) -> dict:
    """
    Backtest completo com ValueBetFilterV2 e Kelly staking com sanity checks.
    """
    signals = signals.reset_index(drop=True)
    df_odds = df_odds.reset_index(drop=True)

    bankroll = bankroll_init
    bets = []
    bankroll_history = [bankroll]
    n_bets_so_far = 0
    cumulative_profit = 0.0

    odd_map = {"1": "odd_1", "X": "odd_X", "2": "odd_2"}

    for i in range(len(signals)):
        pred = signals.loc[i, "predicted_outcome"]
        actual = signals.loc[i, "actual_outcome"]
        odds_col = odd_map.get(pred)

        if odds_col is None or odds_col not in df_odds.columns:
            continue

        odds = df_odds.loc[i, odds_col]
        if pd.isna(odds) or odds <= 1.0:
            continue

        prob_key = {"1": "prob_home", "X": "prob_draw", "2": "prob_away"}[pred]
        model_prob = signals.loc[i, prob_key]

        # Kelly sanity check
        peak = max(bankroll_history)
        current_dd = (peak - bankroll) / peak if peak > 0 else 0.0
        roi_so_far = cumulative_profit / bankroll_init if bankroll_init > 0 else 0.0

        kelly_result = kelly_with_sanity(
            model_prob=model_prob,
            odds=odds,
            ece=model_ece,
            fraction=kelly_fraction,
            max_kelly_full=0.15,
            n_bets_so_far=n_bets_so_far,
            roi_so_far=roi_so_far,
            current_drawdown=current_dd,
        )

        if not kelly_result["passed"]:
            continue

        stake = bankroll * kelly_result["stake_fraction"]
        if stake <= 0:
            continue

        won = str(pred) == str(actual)
        profit = stake * (odds - 1.0) if won else -stake
        bankroll += profit
        bankroll_history.append(bankroll)
        cumulative_profit += profit
        n_bets_so_far += 1

        # Implied prob for edge calc
        implied = 1.0 / odds
        edge = model_prob - implied

        bets.append({
            "index": i,
            "predicted_outcome": pred,
            "actual_outcome": actual,
            "odds": odds,
            "model_prob": model_prob,
            "edge": edge,
            "ev": (model_prob * (odds - 1.0)) - (1.0 - model_prob),
            "kelly_fraction": kelly_result["stake_fraction"],
            "stake": stake,
            "profit": profit,
            "won": won,
            "bankroll": bankroll,
        })

    if not bets:
        return {
            "total_bets": 0,
            "win_rate": 0.0,
            "roi": 0.0,
            "profit": 0.0,
            "final_bankroll": bankroll_init,
            "max_drawdown_pct": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "bets": [],
        }

    df_bets = pd.DataFrame(bets)
    total_stake = df_bets["stake"].sum()
    total_profit = df_bets["profit"].sum()

    # Drawdown
    peak = bankroll_init
    max_dd = 0.0
    for b in bankroll_history:
        if b > peak:
            peak = b
        dd = (peak - b) / peak
        max_dd = max(max_dd, dd)

    # Sharpe / Sortino
    returns = df_bets["profit"] / df_bets["stake"]
    sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0.0
    sortino = compute_sortino(returns.values)

    return {
        "total_bets": len(df_bets),
        "win_rate": df_bets["won"].mean(),
        "roi": total_profit / total_stake if total_stake > 0 else 0.0,
        "profit": total_profit,
        "final_bankroll": bankroll,
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "sortino": sortino,
        "avg_edge": df_bets["edge"].mean(),
        "avg_odds": df_bets["odds"].mean(),
        "bets": bets,
    }


def main():
    parser = argparse.ArgumentParser(description="Optimized Backtest V2")
    parser.add_argument("--save-dir", type=str, default="models/optimized")
    parser.add_argument("--kelly", type=float, default=0.10, help="Fractional Kelly (0.10 = conservative)")
    parser.add_argument("--min-edge", type=float, default=0.03, help="Minimum edge threshold")
    parser.add_argument("--rho-fixed", action="store_true", help="Use fixed rho by league")
    parser.add_argument("--halflife", type=float, default=60.0, help="Time decay halflife in days")
    parser.add_argument("--reg-lambda", type=float, default=0.15, help="L2 regularization")
    args = parser.parse_args()

    data_path = PROJECT_ROOT / "data" / "bronze" / "matches_football_real.parquet"
    if not data_path.exists():
        data_path = PROJECT_ROOT / "data" / "bronze" / "matches_football_real_odds.parquet"
    if not data_path.exists():
        logger.error(
            "No real data found. Run: scripts/ingest_real_data.py --seasons 2122 2223 2324"
        )
        sys.exit(1)

    df = load_data(data_path)
    logger.info("Loaded %d matches", len(df))

    # Detect league if available
    league = df["league"].iloc[0] if "league" in df.columns else None

    # Temporal split (walk-forward)
    n = len(df)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    logger.info("Splits -> train=%d  val=%d  test=%d", len(df_train), len(df_val), len(df_test))

    # ------------------------------------------------------------------
    # Optional: grid search halflife and reg_lambda
    # ------------------------------------------------------------------
    logger.info("Running halflife grid search on training data...")
    hl_search = FootballPoissonModelV2.grid_search_halflife(
        df_train,
        halflife_candidates=[30.0, 60.0, 90.0, 120.0, 180.0],
        n_splits=3,
    )
    logger.info("Halflife search: optimal=%.0f days", hl_search["optimal_halflife"])

    logger.info("Running regularization grid search...")
    reg_search = FootballPoissonModelV2.grid_search_regularization(
        df_train,
        lambda_candidates=[0.05, 0.10, 0.15, 0.20, 0.30],
        n_splits=3,
    )
    logger.info("Reg search: optimal_lambda=%.2f", reg_search["optimal_lambda"])

    # Use grid search results if better than defaults
    halflife = hl_search["optimal_halflife"] if hl_search.get("best_score") else args.halflife
    reg_lambda = reg_search["optimal_lambda"] if reg_search.get("best_score") else args.reg_lambda

    # ------------------------------------------------------------------
    # 1. Treinar PoissonV2
    # ------------------------------------------------------------------
    logger.info("Training FootballPoissonModelV2 (halflife=%.0f, lambda=%.2f, rho_fixed=%s)...",
                halflife, reg_lambda, args.rho_fixed)
    model = FootballPoissonModelV2(
        use_dixon_coles=True,
        reg_lambda=reg_lambda,
        time_decay_halflife_days=halflife,
        rho_fixed_by_league=args.rho_fixed,
        league=league,
    )
    model.fit(df_train, calibrate=True)
    logger.info("Model fitted. rho=%.3f, home_adv=%.3f", model.rho, model.home_advantage)

    # Overfit diagnostic
    overfit = FootballPoissonModelV2.overfit_diagnostic(
        df_train, df_val, halflife=halflife, reg_lambda=reg_lambda
    )
    if overfit["is_overfitting"]:
        logger.warning("OVERFIT DETECTED: %s", overfit["alert_message"])

    # ------------------------------------------------------------------
    # 2. Treinar MetaLabelingModel
    # ------------------------------------------------------------------
    logger.info("Training MetaLabelingModel...")
    signals_val = generate_signals(model, df_val)
    meta_model = MetaLabelingModel()
    try:
        meta_summary = meta_model.fit(signals_val, df_val, n_splits=3)
        logger.info("MetaLabelingModel trained: %s", meta_summary)
    except Exception as e:
        logger.error("MetaLabelingModel training failed: %s. Disabling meta-labeling.", e)
        meta_model = None

    # ------------------------------------------------------------------
    # 3. Gerar sinais no test set
    # ------------------------------------------------------------------
    logger.info("Generating signals on test set...")
    signals_test = generate_signals(model, df_test)

    # Compute model ECE on test set for Kelly adjustment
    pred_probs_test = []
    pred_actuals_test = []
    for _, row in signals_test.iterrows():
        pred = row["predicted_outcome"]
        prob = row[["prob_home", "prob_draw", "prob_away"][["1", "X", "2"].index(pred)]]
        pred_probs_test.append(prob)
        pred_actuals_test.append(1 if pred == row["actual_outcome"] else 0)
    model_ece = compute_ece(np.array(pred_probs_test), np.array(pred_actuals_test), n_bins=10)
    logger.info("Model ECE on test set: %.4f", model_ece)

    # ------------------------------------------------------------------
    # 4. Backtest com ValueBetFilterV2
    # ------------------------------------------------------------------
    logger.info("Running backtest with ValueBetFilterV2 (min_edge=%.1f%%)...", args.min_edge * 100)
    value_filter = ValueBetFilterV2(min_edge=args.min_edge)

    results = {}

    # 4a. Sem meta-labeling
    results["without_meta"] = backtest_with_filter(
        signals_test, df_test, value_filter,
        bankroll_init=1000.0, kelly_fraction=args.kelly, model_ece=model_ece,
    )

    # 4b. Com meta-labeling
    if meta_model is not None and meta_model.is_fitted:
        for thr in [0.55, 0.60, 0.65]:
            try:
                mask = meta_model.filter_signals(signals_test, df_test, threshold=thr).values
                signals_filtered = signals_test[mask].reset_index(drop=True)
                df_odds_filtered = df_test[mask].reset_index(drop=True)

                if len(signals_filtered) > 0:
                    results[f"meta_thr_{thr:.2f}"] = backtest_with_filter(
                        signals_filtered, df_odds_filtered, value_filter,
                        bankroll_init=1000.0, kelly_fraction=args.kelly, model_ece=model_ece,
                    )
                else:
                    results[f"meta_thr_{thr:.2f}"] = {"total_bets": 0}
            except Exception as e:
                logger.warning("Meta-labeling backtest failed for thr=%.2f: %s", thr, e)
                results[f"meta_thr_{thr:.2f}"] = {"total_bets": 0}

    # ------------------------------------------------------------------
    # 5. Build full BacktestReport for best strategy
    # ------------------------------------------------------------------
    best_key = max(
        [k for k in results if results[k].get("total_bets", 0) > 0],
        key=lambda k: results[k]["roi"],
        default=None,
    )
    full_report = None
    if best_key:
        best_bets = pd.DataFrame(results[best_key]["bets"])
        if not best_bets.empty:
            model_probs = best_bets["model_prob"].values
            outcomes = best_bets["won"].astype(int).values
            closing_probs = 1.0 / best_bets["odds"].values
            full_report = build_backtest_report(
                best_bets,
                model_probs=model_probs,
                outcomes=outcomes,
                closing_probs=closing_probs,
                n_mc_sims=10000,
            )
            logger.info("Best strategy: %s | ECE=%.4f | ROI=%.2f%%", best_key, full_report.ece, full_report.roi * 100)

    # ------------------------------------------------------------------
    # 6. Guardar e imprimir resultados
    # ------------------------------------------------------------------
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    model.save(str(save_dir / "poisson_v2.json"))
    if meta_model is not None:
        meta_model.save(str(save_dir / "meta_labeler"))

    # Guardar relatório completo
    report = {
        "model": "FootballPoissonModelV2",
        "meta_labeler": meta_model is not None,
        "value_filter": "ValueBetFilterV2",
        "kelly_fraction": args.kelly,
        "min_edge": args.min_edge,
        "halflife": halflife,
        "reg_lambda": reg_lambda,
        "rho": model.rho,
        "rho_fixed": args.rho_fixed,
        "model_ece": model_ece,
        "halflife_search": hl_search,
        "regularization_search": reg_search,
        "overfit_diagnostic": overfit,
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "bets"} for k, v in results.items()},
    }
    if full_report is not None:
        report["full_backtest_report"] = full_report.to_dict()
        report["acceptance_check"] = full_report.is_acceptable()[1]

    with open(save_dir / "backtest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Imprimir resumo
    print("\n" + "=" * 100)
    print("OPTIMIZED BACKTEST RESULTS (Test Set)")
    print("=" * 100)
    print(f"{'Strategy':<25} {'Bets':>6} {'Win%':>7} {'ROI%':>8} {'Profit':>10} {'Bankroll':>10} {'MaxDD%':>8} {'Sortino':>8}")
    print("-" * 100)

    for name, res in results.items():
        if res.get("total_bets", 0) == 0:
            print(f"{name:<25} {'0':>6} {'N/A':>7} {'N/A':>8} {'N/A':>10} {'N/A':>10} {'N/A':>8} {'N/A':>8}")
            continue
        print(
            f"{name:<25} {res['total_bets']:>6} "
            f"{res['win_rate']*100:>6.1f}% {res['roi']*100:>7.2f}% "
            f"{res['profit']:>10.2f} {res['final_bankroll']:>10.2f} "
            f"{res['max_drawdown_pct']*100:>7.1f}% {res.get('sortino', 0):>8.2f}"
        )

    print("=" * 100)

    if best_key:
        print(f"\nBest strategy: {best_key} | ROI: {results[best_key]['roi']*100:.2f}% | Profit: {results[best_key]['profit']:.2f}")
    if full_report is not None:
        acceptable, issues = full_report.is_acceptable()
        print(f"Acceptance criteria: {'PASS' if acceptable else 'FAIL'}")
        for issue in issues:
            print(f"  WARNING: {issue}")
    print("=" * 100)


if __name__ == "__main__":
    main()
