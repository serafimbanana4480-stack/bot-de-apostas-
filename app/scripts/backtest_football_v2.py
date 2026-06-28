"""
E2E Backtest do sistema de value betting football.
Usa modelo Poisson V2 treinado + ValueBetFilterV2.
"""
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("e2e_backtest")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.ml.models.football_poisson_v2 import FootballPoissonModelV2, _fold_brier_score


def run_backtest(
    train_start: str = "2019-08-01",
    train_end: str = "2022-07-31",
    test_start: str = "2022-08-01",
    test_end: str = "2024-06-30",
    halflife: float = 90.0,
    reg_lambda: float = 0.15,
    min_edge: float = 0.03,
):
    """Run walk-forward backtest with temporal train/test split."""
    logger.info("=== BACKTEST FOOTBALL POISSON V2 ===")
    logger.info("Treino: %s a %s", train_start, train_end)
    logger.info("Teste:  %s a %s", test_start, test_end)

    # Load data
    df = pd.read_parquet(ROOT / "data" / "matches_football_real.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    train_mask = (df["date"] >= train_start) & (df["date"] <= train_end)
    test_mask = (df["date"] >= test_start) & (df["date"] <= test_end)

    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()

    logger.info("Dados de treino: %d jogos", len(train_df))
    logger.info("Dados de teste:  %d jogos", len(test_df))

    if len(train_df) < 500 or len(test_df) < 100:
        logger.error("Dados insuficientes para backtest.")
        return None

    # Train model
    model = FootballPoissonModelV2(
        use_dixon_coles=True,
        reg_lambda=reg_lambda,
        time_decay_halflife_days=halflife,
    )
    model.fit(train_df, calibrate=True)

    # Validate on test set
    bs = _fold_brier_score(model, test_df)
    logger.info("Brier Score no teste: %.4f", bs)
    logger.info("Home advantage: %.3f", model.home_advantage)

    # Generate bets
    from src.risk.value_filter_v2 import ValueBetFilterV2

    filter_v2 = ValueBetFilterV2(
        min_edge=min_edge,
        max_odds=10.0,
        min_odds=1.20,
        require_pinnacle=False,
    )

    bets = []
    for _, row in test_df.iterrows():
        try:
            probs = model.predict_match_outcome(
                row["home_team"], row["away_team"],
                league=row.get("league"), apply_calibration=True,
            )
        except Exception:
            continue

        for outcome, odd_col in [("1", "odd_home"), ("X", "odd_draw"), ("2", "odd_away")]:
            odd = row.get(odd_col, 0)
            if not odd or odd <= 1.0:
                continue
            prob = probs.get(outcome, 0.33)

            # Edge = prob - implied_prob
            implied = 1.0 / odd
            edge = prob - implied

            # Map result to model outcome
            result_map = {"H": "1", "D": "X", "A": "2"}
            actual_outcome = result_map.get(row.get("result", ""), "")

            opp = {
                "model_prob": prob,
                "odds": float(odd),
                "pinnacle_odds": float(row.get(f"pin_close_{outcome}", 0) or 0),
                "edge": float(edge),
                "predicted_outcome": outcome,
                "event_time": row["date"],
                "clv_pct": 0.0,
                "commission_rate": 0.05,
                "has_critical_injury_24h": False,
            }

            passed, reason, metrics = filter_v2.evaluate(opp)
            if passed:
                stakes = filter_v2.kelly_stake(
                    bankroll=10000.0,
                    model_prob=prob,
                    odds=float(odd),
                    fraction=0.25,
                )
                won = actual_outcome == outcome
                profit = stakes * (odd - 1) if won else -stakes
                bets.append({
                    "date": row["date"],
                    "league": row.get("league", ""),
                    "home": row["home_team"],
                    "away": row["away_team"],
                    "outcome": outcome,
                    "odds": float(odd),
                    "prob": round(float(prob), 4),
                    "edge": round(float(edge), 4),
                    "stake": round(stakes, 2),
                    "won": won,
                    "actual": actual_outcome,
                    "profit": round(float(profit), 2),
                    "home_goals": int(row.get("home_goals", 0)),
                    "away_goals": int(row.get("away_goals", 0)),
                })

    if not bets:
        logger.info("❌ NENHUMA APOSTA GERADA. Filtro muito restritivo ou modelo sem edge.")
        return {
            "n_bets": 0,
            "brier_score": bs,
            "message": "No bets generated",
        }

    df_bets = pd.DataFrame(bets)

    # Metrics
    n_bets = len(df_bets)
    win_rate = df_bets["won"].mean()
    total_profit = df_bets["profit"].sum()
    total_stake = df_bets["stake"].sum()
    roi = total_profit / total_stake if total_stake > 0 else 0.0
    best_edge = df_bets["edge"].max()
    avg_edge = df_bets["edge"].mean()
    avg_odds = df_bets["odds"].mean()
    profit_factor = df_bets[df_bets["won"]]["profit"].sum() / abs(df_bets[~df_bets["won"]]["profit"].sum()) if df_bets[~df_bets["won"]]["profit"].sum() != 0 else float("inf")

    logger.info("=" * 60)
    logger.info("RESULTADOS DO BACKTEST")
    logger.info("=" * 60)
    logger.info("Apostas:     %d", n_bets)
    logger.info("Win Rate:    %.1f%%", win_rate * 100)
    logger.info("ROI total:   %.2f%%", roi * 100)
    logger.info("Lucro:       €%.2f", total_profit)
    logger.info("Volume:      €%.2f", total_stake)
    logger.info("Profit Factor: %.2f", profit_factor)
    logger.info("Avg Edge:    %.2f%%", avg_edge * 100)
    logger.info("Best Edge:   %.2f%%", best_edge * 100)
    logger.info("Avg Odds:    %.2f", avg_odds)
    logger.info("Brier Score: %.4f", bs)

    # Distribuição por resultado
    for outcome in ["1", "X", "2"]:
        subset = df_bets[df_bets["outcome"] == outcome]
        if len(subset) > 0:
            logger.info("  %s: %d bets, WR=%.1f%%, ROI=%.1f%%",
                        outcome, len(subset),
                        subset["won"].mean() * 100,
                        (subset["profit"].sum() / subset["stake"].sum()) * 100)

    # Sharpe ratio (proxy)
    if len(df_bets) > 1:
        returns = df_bets["profit"].values / 10000.0
        sharpe = returns.mean() / returns.std() * (365 ** 0.5) if returns.std() > 0 else 0
        logger.info("Sharpe Ratio (anualizado): %.2f", sharpe)

    # Salvar resultados
    report = {
        "n_bets": n_bets,
        "win_rate": round(float(win_rate), 4),
        "roi_pct": round(float(roi), 4),
        "total_profit": round(float(total_profit), 2),
        "total_stake": round(float(total_stake), 2),
        "profit_factor": round(float(profit_factor), 4),
        "avg_edge": round(float(avg_edge), 4),
        "best_edge": round(float(best_edge), 4),
        "avg_odds": round(float(avg_odds), 4),
        "brier_score": round(float(bs), 4),
        "train_matches": len(train_df),
        "test_matches": len(test_df),
        "date_range": f"{test_start} to {test_end}",
    }

    logger.info("=== Backtest completo ===")
    return report, df_bets


if __name__ == "__main__":
    result = run_backtest(
        train_start="2019-08-01",
        train_end="2022-07-31",
        test_start="2022-08-01",
        test_end="2024-06-30",
        halflife=90.0,
        reg_lambda=0.15,
        min_edge=0.03,
    )
    if result is not None:
        report, df_bets = result
        # Save report
        import json
        report_path = ROOT / "data" / "reports" / "backtest_v2_football.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Relatório salvo em %s", report_path)

        # Show top 10 bets
        print("\nTop 10 melhores apostas (por edge):")
        print(df_bets.sort_values("edge", ascending=False).head(10).to_string())
