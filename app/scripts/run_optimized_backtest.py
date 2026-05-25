#!/usr/bin/env python3
"""
Optimized Backtest — Modelo PoissonV2 + ValueBetFilterV2 + MetaLabeling.

Este script representa a versão mais avançada do sistema, incorporando:
  1. FootballPoissonModelV2 (MLE + decay temporal + rho estimado)
  2. ValueBetFilterV2 (edge-based, sem filtro de probabilidade)
  3. MetaLabeler (filtra sinais fracos com market features)
  4. Kelly Criterion (quarter-Kelly com calibração)
  5. Walk-forward temporal honesto

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

from src.ml.meta_labeling import MetaLabeler, evaluate_meta_labeling
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
        "actual_outcome", "open_odd_home", "pin_close_home",
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
    kelly_fraction: float = 0.25,
) -> dict:
    """
    Backtest completo com ValueBetFilterV2 e Kelly staking.
    """
    signals = signals.reset_index(drop=True)
    df_odds = df_odds.reset_index(drop=True)

    bankroll = bankroll_init
    bets = []
    bankroll_history = [bankroll]

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

        # Probabilidade do modelo para o outcome predito
        prob_key = {"1": "prob_home", "X": "prob_draw", "2": "prob_away"}[pred]
        model_prob = signals.loc[i, prob_key]

        # Criar oportunidade
        opp = {
            "match_id": f"match_{i}",
            "event_name": f"{df_odds.loc[i, 'home_team']} vs {df_odds.loc[i, 'away_team']}",
            "model_prob": model_prob,
            "odds": odds,
            "pinnacle_odds": df_odds.loc[i, "pin_close_home"] if pred == "1" else None,
            "clv_pct": 0.0,  # Simplificado
        }

        passed, reason, metrics = value_filter.evaluate(opp)

        if not passed:
            continue

        # Calcular stake via Kelly
        stake = value_filter.kelly_stake(bankroll, model_prob, odds, fraction=kelly_fraction)
        if stake <= 0:
            continue

        # Simular resultado
        won = str(pred) == str(actual)
        profit = stake * (odds - 1.0) if won else -stake
        bankroll += profit
        bankroll_history.append(bankroll)

        bets.append({
            "index": i,
            "predicted_outcome": pred,
            "actual_outcome": actual,
            "odds": odds,
            "model_prob": model_prob,
            "edge": metrics["edge"],
            "ev": metrics["expected_value"],
            "kelly_fraction": metrics["kelly_fraction"],
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

    # Sharpe proxy (simplificado)
    returns = df_bets["profit"] / df_bets["stake"]
    sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0.0

    return {
        "total_bets": len(df_bets),
        "win_rate": df_bets["won"].mean(),
        "roi": total_profit / total_stake if total_stake > 0 else 0.0,
        "profit": total_profit,
        "final_bankroll": bankroll,
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "avg_edge": df_bets["edge"].mean(),
        "avg_odds": df_bets["odds"].mean(),
        "bets": bets,
    }


def main():
    parser = argparse.ArgumentParser(description="Optimized Backtest V2")
    parser.add_argument("--save-dir", type=str, default="models/optimized")
    parser.add_argument("--kelly", type=float, default=0.25, help="Fractional Kelly (0.25 = quarter-Kelly)")
    parser.add_argument("--min-edge", type=float, default=0.03, help="Minimum edge threshold")
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
    # 1. Treinar PoissonV2
    # ------------------------------------------------------------------
    logger.info("Training FootballPoissonModelV2...")
    model = FootballPoissonModelV2(
        use_dixon_coles=True,
        reg_lambda=0.15,
        time_decay_halflife_days=365.0,
    )
    model.fit(df_train, calibrate=True)
    logger.info("Model fitted. rho=%.3f, home_adv=%.3f", model.rho, model.home_advantage)

    # ------------------------------------------------------------------
    # 2. Treinar MetaLabeler
    # ------------------------------------------------------------------
    logger.info("Training MetaLabeler...")
    signals_val = generate_signals(model, df_val)
    meta_labeler = MetaLabeler(calibrate=True)
    meta_summary = meta_labeler.fit(signals_val, df_val, n_splits=3)
    logger.info("MetaLabeler trained: %s", meta_summary)

    # ------------------------------------------------------------------
    # 3. Gerar sinais no test set
    # ------------------------------------------------------------------
    logger.info("Generating signals on test set...")
    signals_test = generate_signals(model, df_test)

    # ------------------------------------------------------------------
    # 4. Backtest com ValueBetFilterV2
    # ------------------------------------------------------------------
    logger.info("Running backtest with ValueBetFilterV2 (min_edge=%.1f%%)...", args.min_edge * 100)
    value_filter = ValueBetFilterV2(min_edge=args.min_edge)

    results = {}

    # 4a. Sem meta-labeling
    results["without_meta"] = backtest_with_filter(
        signals_test, df_test, value_filter,
        bankroll_init=1000.0, kelly_fraction=args.kelly,
    )

    # 4b. Com meta-labeling em diferentes thresholds
    for thr in [0.55, 0.60, 0.65]:
        probs_meta = meta_labeler.predict(market_features=df_test)
        mask = probs_meta >= thr

        signals_filtered = signals_test[mask].reset_index(drop=True)
        df_odds_filtered = df_test[mask].reset_index(drop=True)

        if len(signals_filtered) > 0:
            results[f"meta_thr_{thr:.2f}"] = backtest_with_filter(
                signals_filtered, df_odds_filtered, value_filter,
                bankroll_init=1000.0, kelly_fraction=args.kelly,
            )
        else:
            results[f"meta_thr_{thr:.2f}"] = {"total_bets": 0}

    # ------------------------------------------------------------------
    # 5. Guardar e imprimir resultados
    # ------------------------------------------------------------------
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    model.save(str(save_dir / "poisson_v2.json"))
    meta_labeler.save(str(save_dir / "meta_labeler"))

    # Guardar relatório
    report = {
        "model": "FootballPoissonModelV2",
        "meta_labeler": True,
        "value_filter": "ValueBetFilterV2",
        "kelly_fraction": args.kelly,
        "min_edge": args.min_edge,
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "bets"} for k, v in results.items()},
    }
    with open(save_dir / "backtest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Imprimir resumo
    print("\n" + "=" * 80)
    print("OPTIMIZED BACKTEST RESULTS (Test Set)")
    print("=" * 80)
    print(f"{'Strategy':<25} {'Bets':>6} {'Win%':>7} {'ROI%':>8} {'Profit':>10} {'Bankroll':>10} {'MaxDD%':>8}")
    print("-" * 80)

    for name, res in results.items():
        if res.get("total_bets", 0) == 0:
            print(f"{name:<25} {'0':>6} {'N/A':>7} {'N/A':>8} {'N/A':>10} {'N/A':>10} {'N/A':>8}")
            continue
        print(
            f"{name:<25} {res['total_bets']:>6} "
            f"{res['win_rate']*100:>6.1f}% {res['roi']*100:>7.2f}% "
            f"{res['profit']:>10.2f} {res['final_bankroll']:>10.2f} "
            f"{res['max_drawdown_pct']*100:>7.1f}%"
        )

    print("=" * 80)

    best = max(
        [(k, v) for k, v in results.items() if v.get("total_bets", 0) > 0],
        key=lambda x: x[1]["roi"],
        default=(None, None),
    )
    if best[0]:
        print(f"\nBest strategy: {best[0]} | ROI: {best[1]['roi']*100:.2f}% | Profit: {best[1]['profit']:.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
