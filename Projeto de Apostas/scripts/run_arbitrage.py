#!/usr/bin/env python3
"""
Arbitrage Execution Script

Executa deteção de arbitragem em dados reais de odds, calcula stakes exatas
para lucro garantido, e gera CSV de oportunidades acionáveis.

Usage:
    poetry run python scripts/run_arbitrage.py --paper --bankroll 1000
    poetry run python scripts/run_arbitrage.py --no-paper --bankroll 5000 --min-profit 0.5
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger("run_arbitrage")


def implied_probability(odds: float) -> float:
    """Calcula probabilidade implícita a partir das odds."""
    if odds is None or odds <= 1.0:
        return 1.0
    return 1.0 / odds


def calculate_arbitrage_stakes(
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    bankroll: float,
) -> Optional[Dict]:
    """
    Calcula stakes para arbitragem garantida.

    Returns None se não houver arbitragem.
    """
    p_home = implied_probability(odds_home)
    p_draw = implied_probability(odds_draw)
    p_away = implied_probability(odds_away)

    total_implied = p_home + p_draw + p_away

    if total_implied >= 1.0:
        return None

    profit_pct = (1.0 / total_implied - 1.0) * 100.0

    stake_home = (p_home / total_implied) * bankroll
    stake_draw = (p_draw / total_implied) * bankroll
    stake_away = (p_away / total_implied) * bankroll

    # Payout é igual independentemente do resultado
    payout = stake_home * odds_home

    return {
        "total_implied": total_implied,
        "profit_pct": profit_pct,
        "stake_home": round(stake_home, 2),
        "stake_draw": round(stake_draw, 2),
        "stake_away": round(stake_away, 2),
        "stake_total": round(stake_home + stake_draw + stake_away, 2),
        "payout": round(payout, 2),
        "profit": round(payout - bankroll, 2),
        "odds_home": odds_home,
        "odds_draw": odds_draw,
        "odds_away": odds_away,
    }


def detect_arbitrage_for_match(row: pd.Series) -> List[Dict]:
    """
    Deteta todas as combinações de arbitragem possíveis para um jogo,
    comparando b365 vs Pinnacle (pin_close) vs max odds.
    """
    opportunities = []

    bookmakers = {
        "b365": {"home": row.get("b365_home"), "draw": row.get("b365_draw"), "away": row.get("b365_away")},
        "pinnacle": {"home": row.get("pin_close_home"), "draw": row.get("pin_close_draw"), "away": row.get("pin_close_away")},
        "max": {"home": row.get("max_home"), "draw": row.get("max_draw"), "away": row.get("max_away")},
    }

    # Todas as combinações de 3 bookmakers (um por resultado)
    for home_book, home_odds in [(k, v["home"]) for k, v in bookmakers.items()]:
        for draw_book, draw_odds in [(k, v["draw"]) for k, v in bookmakers.items()]:
            for away_book, away_odds in [(k, v["away"]) for k, v in bookmakers.items()]:
                if pd.isna(home_odds) or pd.isna(draw_odds) or pd.isna(away_odds):
                    continue
                if home_odds <= 1.0 or draw_odds <= 1.0 or away_odds <= 1.0:
                    continue

                arb = calculate_arbitrage_stakes(home_odds, draw_odds, away_odds, bankroll=100.0)
                if arb is not None:
                    arb["home_bookmaker"] = home_book
                    arb["draw_bookmaker"] = draw_book
                    arb["away_bookmaker"] = away_book
                    arb["match_id"] = row.get("match_id", "unknown")
                    arb["date"] = row.get("date")
                    arb["home_team"] = row.get("home_team")
                    arb["away_team"] = row.get("away_team")
                    arb["league"] = row.get("league")
                    opportunities.append(arb)

    return opportunities


def find_best_arbitrage(row: pd.Series) -> Optional[Dict]:
    """Encontra a melhor oportunidade de arbitragem para um jogo."""
    opportunities = detect_arbitrage_for_match(row)
    if not opportunities:
        return None
    return max(opportunities, key=lambda x: x["profit_pct"])


def run_arbitrage_detection(
    df: pd.DataFrame,
    bankroll: float,
    min_profit_pct: float,
) -> pd.DataFrame:
    """
    Corre deteção de arbitragem em todo o DataFrame e retorna oportunidades acionáveis.
    """
    results = []

    for _, row in df.iterrows():
        best = find_best_arbitrage(row)
        if best and best["profit_pct"] >= min_profit_pct:
            # Recalcular stakes com o bankroll real
            stakes = calculate_arbitrage_stakes(
                best["odds_home"],
                best["odds_draw"],
                best["odds_away"],
                bankroll,
            )
            if stakes:
                stakes.update({
                    "home_bookmaker": best["home_bookmaker"],
                    "draw_bookmaker": best["draw_bookmaker"],
                    "away_bookmaker": best["away_bookmaker"],
                    "date": best["date"],
                    "home_team": best["home_team"],
                    "away_team": best["away_team"],
                    "league": best["league"],
                })
                results.append(stakes)

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


def main(args: argparse.Namespace) -> None:
    data_path = Path("data/bronze/matches_football_real_odds.parquet")
    if not data_path.exists():
        logger.error(f"Ficheiro não encontrado: {data_path}")
        sys.exit(1)

    logger.info(f"A carregar dados de {data_path}...")
    df = pd.read_parquet(data_path)
    logger.info(f"Total de jogos carregados: {len(df)}")

    # Garantir match_id
    if "match_id" not in df.columns:
        df["match_id"] = df.index.astype(str)

    opportunities = run_arbitrage_detection(
        df,
        bankroll=args.bankroll,
        min_profit_pct=args.min_profit,
    )

    logger.info(f"\n{'='*80}")
    logger.info(f"RESULTADOS DA ARBITRAGEM")
    logger.info(f"{'='*80}")
    logger.info(f"Total de jogos analisados: {len(df)}")
    logger.info(f"Oportunidades encontradas: {len(opportunities)}")

    if not opportunities.empty:
        logger.info(f"Lucro médio: {opportunities['profit_pct'].mean():.2f}%")
        logger.info(f"Melhor lucro: {opportunities['profit_pct'].max():.2f}%")
        logger.info(f"Lucro total garantido (bankroll {args.bankroll}): {opportunities['profit'].sum():.2f}")

        # Ordenar por lucro
        opportunities = opportunities.sort_values("profit_pct", ascending=False)

        logger.info(f"\n{'='*80}")
        logger.info(f"TOP {min(10, len(opportunities))} OPORTUNIDADES")
        logger.info(f"{'='*80}")
        for _, row in opportunities.head(10).iterrows():
            logger.info(
                f"{row['home_team']} vs {row['away_team']} ({row['league']}) — "
                f"Lucro: {row['profit_pct']:.2f}% | "
                f"Casa: {row['home_bookmaker']} @ {row['odds_home']:.2f} ({row['stake_home']:.2f}) | "
                f"Empate: {row['draw_bookmaker']} @ {row['odds_draw']:.2f} ({row['stake_draw']:.2f}) | "
                f"Fora: {row['away_bookmaker']} @ {row['odds_away']:.2f} ({row['stake_away']:.2f})"
            )

        # Exportar CSV
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        csv_cols = [
            "date", "league", "home_team", "away_team",
            "profit_pct", "profit",
            "home_bookmaker", "odds_home", "stake_home",
            "draw_bookmaker", "odds_draw", "stake_draw",
            "away_bookmaker", "odds_away", "stake_away",
            "stake_total", "payout",
        ]
        opportunities[csv_cols].to_csv(output_path, index=False)
        logger.info(f"\nOportunidades exportadas para {output_path}")

        if args.paper:
            logger.info("\n[MODO PAPER] — Nenhuma aposta foi colocada. Use --no-paper para execução real.")
        else:
            logger.warning("\n[MODO REAL] — Execução de apostas ainda não implementada. MODO PAPER ativado por segurança.")
    else:
        logger.info("Nenhuma oportunidade de arbitragem encontrada com os critérios atuais.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execução de Arbitragem em Dados Reais")
    parser.add_argument("--paper", action=argparse.BooleanOptionalAction, default=True,
                        help="Modo paper (default: True). Apenas imprime oportunidades sem colocar apostas.")
    parser.add_argument("--bankroll", type=float, default=1000.0,
                        help="Bankroll total para dimensionar stakes proporcionalmente")
    parser.add_argument("--min-profit", type=float, default=0.5,
                        help="Lucro mínimo em percentagem para considerar oportunidade")
    parser.add_argument("--output", default="data/reports/arbitrage_opportunities.csv",
                        help="Caminho para o CSV de output")

    args = parser.parse_args()
    main(args)
