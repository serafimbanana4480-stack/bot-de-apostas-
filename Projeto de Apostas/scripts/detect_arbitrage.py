#!/usr/bin/env python3
"""
Arbitrage Detector - Detecta oportunidades de arbitragem entre bookmakers

Arbitragem = apostar em todos os resultados de um evento em diferentes bookmakers
com lucro garantido independentemente do resultado.

Exemplo:
- Casa A: Vitória Casa @ 2.10 (47.6% implied)
- Casa B: Empate @ 3.50 (28.6% implied)  
- Casa C: Vitória Fora @ 3.10 (32.3% implied)
- Total implied = 108.5% → Arbitragem possível (se < 100%)

Lucro garantido = (1 / total_implied) - 1 = 7.8%

Usage:
    poetry run python scripts/detect_arbitrage.py --sport football
    poetry run python scripts/detect_arbitrage.py --sport football --min-profit 1.5
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger("arbitrage_detector")


class ArbitrageDetector:
    """
    Detecta oportunidades de arbitragem comparando odds entre múltiplos bookmakers.
    """
    
    def __init__(self, min_profit_pct: float = 1.0):
        """
        Args:
            min_profit_pct: Lucro mínimo em percentagem para considerar arbitragem
        """
        self.min_profit_pct = min_profit_pct
        self.logger = logging.getLogger("arbitrage_detector")
        
    def calculate_implied_prob(self, odds: float) -> float:
        """Calcula probabilidade implícita das odds (com overround)."""
        if odds <= 1.0:
            return 1.0
        return 1.0 / odds
    
    def check_arbitrage_opportunity(
        self,
        odds_home: List[Tuple[str, float]],  # [(bookmaker, odds), ...]
        odds_draw: List[Tuple[str, float]],
        odds_away: List[Tuple[str, float]]
    ) -> Optional[Dict]:
        """
        Verifica se existe oportunidade de arbitragem para um evento.
        
        Args:
            odds_home: Lista de (bookmaker, odds) para vitória casa
            odds_draw: Lista de (bookmaker, odds) para empate
            odds_away: Lista de (bookmaker, odds) para vitória fora
            
        Returns:
            Dict com detalhes da arbitragem ou None se não houver oportunidade
        """
        if not odds_home or not odds_draw or not odds_away:
            return None
            
        # Encontrar melhores odds para cada resultado
        best_home = max(odds_home, key=lambda x: x[1])
        best_draw = max(odds_draw, key=lambda x: x[1])
        best_away = max(odds_away, key=lambda x: x[1])
        
        # Calcular probabilidades implícitas
        prob_home = self.calculate_implied_prob(best_home[1])
        prob_draw = self.calculate_implied_prob(best_draw[1])
        prob_away = self.calculate_implied_prob(best_away[1])
        
        total_implied = prob_home + prob_draw + prob_away
        
        # Se total < 100%, existe arbitragem
        if total_implied < 1.0:
            profit_pct = (1.0 / total_implied - 1.0) * 100
            
            if profit_pct >= self.min_profit_pct:
                # Calcular stake proporcional para cada aposta
                # Fórmula: stake = (implied_prob / total_implied) * bankroll
                stake_home_pct = (prob_home / total_implied) * 100
                stake_draw_pct = (prob_draw / total_implied) * 100
                stake_away_pct = (prob_away / total_implied) * 100
                
                return {
                    "is_arbitrage": True,
                    "profit_pct": profit_pct,
                    "total_implied_pct": total_implied * 100,
                    "best_combination": {
                        "home": {"bookmaker": best_home[0], "odds": best_home[1], "stake_pct": stake_home_pct},
                        "draw": {"bookmaker": best_draw[0], "odds": best_draw[1], "stake_pct": stake_draw_pct},
                        "away": {"bookmaker": best_away[0], "odds": best_away[1], "stake_pct": stake_away_pct},
                    },
                    "all_odds": {
                        "home": odds_home,
                        "draw": odds_draw,
                        "away": odds_away
                    }
                }
        
        return None
    
    def detect_arbitrages_from_dataframe(
        self,
        df: pd.DataFrame,
        bookmaker_cols: Dict[str, List[str]]
    ) -> List[Dict]:
        """
        Detecta arbitragens a partir de um DataFrame com odds de múltiplos bookmakers.
        
        Args:
            df: DataFrame com colunas de odds
            bookmaker_cols: Dict mapping resultado to lista de colunas de odds por bookmaker
                Ex: {
                    "home": ["pinnacle_home", "bet365_home", "william_hill_home"],
                    "draw": ["pinnacle_draw", "bet365_draw", "william_hill_draw"],
                    "away": ["pinnacle_away", "bet365_away", "william_hill_away"]
                }
                
        Returns:
            Lista de oportunidades de arbitragem
        """
        arbitrages = []
        
        for _, row in df.iterrows():
            odds_home = []
            odds_draw = []
            odds_away = []
            
            # Extrair odds de cada bookmaker
            for col in bookmaker_cols.get("home", []):
                if col in row and pd.notna(row[col]) and row[col] > 1.0:
                    bookmaker = col.split("_")[0]  # Extrair nome do bookmaker
                    odds_home.append((bookmaker, float(row[col])))
            
            for col in bookmaker_cols.get("draw", []):
                if col in row and pd.notna(row[col]) and row[col] > 1.0:
                    bookmaker = col.split("_")[0]
                    odds_draw.append((bookmaker, float(row[col])))
            
            for col in bookmaker_cols.get("away", []):
                if col in row and pd.notna(row[col]) and row[col] > 1.0:
                    bookmaker = col.split("_")[0]
                    odds_away.append((bookmaker, float(row[col])))
            
            # Verificar arbitragem
            arb = self.check_arbitrage_opportunity(odds_home, odds_draw, odds_away)
            if arb:
                arb["match_info"] = {
                    "home_team": row.get("home_team"),
                    "away_team": row.get("away_team"),
                    "date": row.get("date"),
                    "league": row.get("league")
                }
                arbitrages.append(arb)
        
        return arbitrages
    
    def generate_synthetic_arbitrage_data(
        self,
        n_matches: int = 100,
        n_bookmakers: int = 5
    ) -> pd.DataFrame:
        """
        Gera dados sintéticos para testar o detector de arbitragem.
        """
        np.random.seed(42)
        
        bookmakers = [f"bookmaker_{i}" for i in range(1, n_bookmakers + 1)]
        
        data = []
        dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n_matches)]
        
        for i, date in enumerate(dates):
            # Gerar probabilidades reais (somam 100%)
            real_probs = np.random.dirichlet([1, 1, 1])  # home, draw, away
            
            # Para cada bookmaker, gerar odds com overround aleatório (2-8%)
            row = {
                "match_id": f"match_{i}",
                "date": date,
                "home_team": f"Team_{np.random.randint(1, 100)}",
                "away_team": f"Team_{np.random.randint(1, 100)}",
                "league": "Synthetic League"
            }
            
            for bm in bookmakers:
                overround = np.random.uniform(0.02, 0.08)
                
                # Aplicar overround às probabilidades
                probs_with_overround = real_probs * (1 + overround)
                
                # Converter para odds
                odds_home = 1.0 / probs_with_overround[0] if probs_with_overround[0] > 0 else 2.0
                odds_draw = 1.0 / probs_with_overround[1] if probs_with_overround[1] > 0 else 3.0
                odds_away = 1.0 / probs_with_overround[2] if probs_with_overround[2] > 0 else 3.0
                
                row[f"{bm}_home"] = round(odds_home, 2)
                row[f"{bm}_draw"] = round(odds_draw, 2)
                row[f"{bm}_away"] = round(odds_away, 2)
            
            # Ocasionalmente criar arbitragem intencional (5% dos jogos)
            if np.random.random() < 0.05:
                # Criar combinação que dá arbitragem
                best_home_idx = np.random.randint(0, n_bookmakers)
                best_draw_idx = np.random.randint(0, n_bookmakers)
                best_away_idx = np.random.randint(0, n_bookmakers)
                
                # Aumentar odds nestes bookmakers
                row[f"{bookmakers[best_home_idx]}_home"] = round(row[f"{bookmakers[best_home_idx]}_home"] * 1.15, 2)
                row[f"{bookmakers[best_draw_idx]}_draw"] = round(row[f"{bookmakers[best_draw_idx]}_draw"] * 1.15, 2)
                row[f"{bookmakers[best_away_idx]}_away"] = round(row[f"{bookmakers[best_away_idx]}_away"] * 1.15, 2)
            
            data.append(row)
        
        return pd.DataFrame(data)


def main(args: argparse.Namespace):
    detector = ArbitrageDetector(min_profit_pct=args.min_profit)
    
    if args.mode == "synthetic":
        logger.info("Gerando dados sintéticos para teste...")
        df = detector.generate_synthetic_arbitrage_data(
            n_matches=args.n_matches,
            n_bookmakers=args.n_bookmakers
        )
        
        # Definir colunas de odds
        bookmakers = [f"bookmaker_{i}" for i in range(1, args.n_bookmakers + 1)]
        bookmaker_cols = {
            "home": [f"{bm}_home" for bm in bookmakers],
            "draw": [f"{bm}_draw" for bm in bookmakers],
            "away": [f"{bm}_away" for bm in bookmakers]
        }
        
    elif args.mode == "real":
        logger.info("Carregando dados reais...")
        try:
            from src.data.local_store import LocalDataStore
            store = LocalDataStore(settings.DATA_DIR)
            df = store.load_parquet(args.dataset)
            
            if df is None or df.empty:
                logger.error(f"Dataset {args.dataset} não encontrado ou vazio")
                return
            
            # Tentar inferir colunas de odds automaticamente
            bookmaker_cols = infer_bookmaker_columns(df)
            logger.info(f"Colunas inferidas: {bookmaker_cols}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados reais: {e}")
            logger.info("Usando modo synthetic em vez disso")
            args.mode = "synthetic"
            df = detector.generate_synthetic_arbitrage_data()
            bookmakers = [f"bookmaker_{i}" for i in range(1, 6)]
            bookmaker_cols = {
                "home": [f"{bm}_home" for bm in bookmakers],
                "draw": [f"{bm}_draw" for bm in bookmakers],
                "away": [f"{bm}_away" for bm in bookmakers]
            }
    else:
        logger.error(f"Modo desconhecido: {args.mode}")
        return
    
    # Detectar arbitragens
    logger.info(f"Detectando arbitragens em {len(df)} jogos...")
    arbitrages = detector.detect_arbitrages_from_dataframe(df, bookmaker_cols)
    
    # Reportar resultados
    logger.info(f"\n{'='*80}")
    logger.info(f"RESULTADOS DA DETEÇÃO DE ARBITRAGEM")
    logger.info(f"{'='*80}")
    logger.info(f"Total de jogos analisados: {len(df)}")
    logger.info(f"Arbitragens encontradas: {len(arbitrages)}")
    logger.info(f"Taxa de arbitragem: {len(arbitrages)/len(df)*100:.2f}%")
    
    if arbitrages:
        logger.info(f"\n{'='*80}")
        logger.info(f"TOP {min(10, len(arbitrages))} MELHORES OPORTUNIDADES")
        logger.info(f"{'='*80}")
        
        # Ordenar por lucro
        arbitrages_sorted = sorted(arbitrages, key=lambda x: x["profit_pct"], reverse=True)
        
        for i, arb in enumerate(arbitrages_sorted[:10], 1):
            match_info = arb["match_info"]
            logger.info(f"\n#{i} - {match_info.get('home_team', 'N/A')} vs {match_info.get('away_team', 'N/A')}")
            logger.info(f"  Data: {match_info.get('date', 'N/A')}")
            logger.info(f"  Lucro garantido: {arb['profit_pct']:.2f}%")
            logger.info(f"  Combinação ótima:")
            
            for outcome, details in arb["best_combination"].items():
                logger.info(f"    {outcome.upper()}: {details['bookmaker']} @ {details['odds']:.2f} (stake: {details['stake_pct']:.1f}%)")
    
    # Exportar resultados
    if arbitrages and args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_df = pd.DataFrame([{
            "match_id": arb["match_info"].get("match_id", f"arb_{i}"),
            "home_team": arb["match_info"].get("home_team"),
            "away_team": arb["match_info"].get("away_team"),
            "date": arb["match_info"].get("date"),
            "profit_pct": arb["profit_pct"],
            "total_implied_pct": arb["total_implied_pct"],
            "best_home_bookmaker": arb["best_combination"]["home"]["bookmaker"],
            "best_home_odds": arb["best_combination"]["home"]["odds"],
            "best_draw_bookmaker": arb["best_combination"]["draw"]["bookmaker"],
            "best_draw_odds": arb["best_combination"]["draw"]["odds"],
            "best_away_bookmaker": arb["best_combination"]["away"]["bookmaker"],
            "best_away_odds": arb["best_combination"]["away"]["odds"],
        } for i, arb in enumerate(arbitrages)])
        
        results_df.to_csv(output_path, index=False)
        logger.info(f"\nResultados exportados para {output_path}")


def infer_bookmaker_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Tenta inferir colunas de odds por bookmaker a partir do DataFrame.
    """
    bookmaker_cols = {"home": [], "draw": [], "away": []}
    
    # Padrões comuns de nomes de colunas
    patterns = {
        "home": ["home", "1", "h"],
        "draw": ["draw", "x", "d"],
        "away": ["away", "2", "a"]
    }
    
    for col in df.columns:
        col_lower = col.lower()
        for outcome, patterns_list in patterns.items():
            if any(p in col_lower for p in patterns_list):
                # Verificar se contém números (odds)
                sample = df[col].dropna().head()
                if len(sample) > 0 and all(isinstance(x, (int, float)) and x > 1.0 for x in sample):
                    bookmaker_cols[outcome].append(col)
    
    # Remover duplicados e ordenar
    for outcome in bookmaker_cols:
        bookmaker_cols[outcome] = list(set(bookmaker_cols[outcome]))
    
    logger.info(f"Colunas inferidas: {bookmaker_cols}")
    
    # Se não encontrou colunas suficientes, usar defaults
    if len(bookmaker_cols["home"]) < 2:
        logger.warning("Não foi possível inferir colunas suficientes. Usando defaults...")
        # Tentar encontrar quaisquer colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        logger.info(f"Colunas numéricas disponíveis: {numeric_cols[:10]}")
    
    return bookmaker_cols


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detector de Arbitragem")
    parser.add_argument("--mode", choices=["synthetic", "real"], default="synthetic",
                        help="Modo de operação")
    parser.add_argument("--dataset", default="matches_football_real_odds",
                        help="Nome do dataset (modo real)")
    parser.add_argument("--n-matches", type=int, default=100,
                        help="Número de jogos para dados sintéticos")
    parser.add_argument("--n-bookmakers", type=int, default=5,
                        help="Número de bookmakers para dados sintéticos")
    parser.add_argument("--min-profit", type=float, default=1.0,
                        help="Lucro mínimo em percentagem")
    parser.add_argument("--output", default="data/reports/arbitrage_opportunities.csv",
                        help="Ficheiro de output para oportunidades")
    
    args = parser.parse_args()
    
    main(args)
