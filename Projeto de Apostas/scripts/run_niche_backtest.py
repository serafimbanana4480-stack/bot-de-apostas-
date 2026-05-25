#!/usr/bin/env python3
"""
Niche Market Backtest Runner

Executa backtest da estratégia de mercados de nicho em dados reais de odds,
imprime métricas e guarda relatório em JSON.

Usage:
    poetry run python scripts/run_niche_backtest.py
    poetry run python scripts/run_niche_backtest.py --stake-pct 0.02 --output data/reports/niche_backtest.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.niche_pipeline import NicheMarketStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger("run_niche_backtest")


def main(args: argparse.Namespace) -> None:
    data_path = Path("data/bronze/matches_football_real_odds.parquet")
    if not data_path.exists():
        logger.error(f"Ficheiro não encontrado: {data_path}")
        sys.exit(1)

    logger.info(f"A carregar dados de {data_path}...")
    df = pd.read_parquet(data_path)
    logger.info(f"Total de jogos carregados: {len(df)}")

    strategy = NicheMarketStrategy()
    metrics = strategy.backtest(df, stake_pct=args.stake_pct)

    logger.info(f"\n{'='*60}")
    logger.info(f"NICHE MARKET BACKTEST RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"Total bets (niche only): {metrics['total_bets']}")
    logger.info(f"Win rate: {metrics['win_rate']:.2%}")
    logger.info(f"ROI: {metrics['roi']:.2%}")
    logger.info(f"Profit (units): {metrics['profit_units']:.2f}")
    logger.info(f"Avg odds: {metrics['avg_odds']:.2f}")

    if metrics.get("feature_importance"):
        logger.info(f"\nFeature Importances:")
        for feat, imp in sorted(metrics["feature_importance"].items(), key=lambda x: -x[1]):
            logger.info(f"  {feat}: {imp:.4f}")

    # Guardar relatório
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"\nRelatório guardado em {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Niche Market Backtest Runner")
    parser.add_argument("--stake-pct", type=float, default=0.01,
                        help="Percentagem do bankroll a apostar por jogo")
    parser.add_argument("--output", default="data/reports/niche_backtest.json",
                        help="Caminho para o ficheiro de relatório JSON")

    args = parser.parse_args()
    main(args)
