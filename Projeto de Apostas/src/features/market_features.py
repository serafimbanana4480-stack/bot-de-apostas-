"""
Market Features - Features baseadas em movimento de odds e dados de mercado

Estas features capturam informação de mercado que o modelo Poisson ignora:
- Line movement (open vs closing odds)
- Steam moves (mudanças rápidas de odds)
- Sharp vs retail money proxies
- Reversal patterns

Estas features são essenciais para:
1. Identificar quando sharp money está movendo as odds
2. Meta-labeling (prever se o sinal do modelo está correto)
3. Filtro de qualidade (evitar jogos com movimento suspeito)
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("market_features")


class MarketFeatures:
    """
    Calcula features baseadas em dados de mercado de odds.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("market_features")
    
    def calculate_line_movement_features(
        self,
        odds_open: pd.Series,
        odds_close: pd.Series,
        odds_current: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calcula features de movimento de linha.
        
        Args:
            odds_open: Odds de abertura
            odds_close: Odds de fecho
            odds_current: Odds atuais (opcional)
            
        Returns:
            DataFrame com features de line movement
        """
        features = pd.DataFrame()
        
        # Movimento absoluto (open -> close)
        features["line_move_abs_home"] = (odds_close - odds_open).abs()
        
        # Movimento percentual (open -> close)
        features["line_move_pct_home"] = ((odds_close - odds_open) / odds_open) * 100
        
        # Direção do movimento (1 = odds subiram, -1 = odds desceram)
        features["line_direction_home"] = np.sign(odds_close - odds_open)
        
        # Magnitude do movimento (se > 5%, é significativo)
        features["line_move_significant_home"] = (features["line_move_pct_home"].abs() > 5).astype(int)
        
        # Se temos odds atuais, calcular movimento adicional
        if odds_current is not None:
            features["line_move_open_to_current_home"] = ((odds_current - odds_open) / odds_open) * 100
            features["line_move_close_to_current_home"] = ((odds_current - odds_close) / odds_close) * 100
        
        return features
    
    def calculate_steam_move_features(
        self,
        odds_history: List[List[float]],
        time_threshold: int = 60
    ) -> pd.DataFrame:
        """
        Detecta steam moves (mudanças rápidas de odds).
        
        Args:
            odds_history: Lista histórica de odds para cada resultado
            time_threshold: Tempo em minutos para considerar mudança "rápida"
            
        Returns:
            DataFrame com features de steam move
        """
        features = pd.DataFrame()
        
        if not odds_history or len(odds_history[0]) < 2:
            return features
        
        # Para cada jogo, calcular mudanças rápidas
        steam_detected = []
        steam_magnitude = []
        
        for game_odds in odds_history:
            if len(game_odds) < 2:
                steam_detected.append(0)
                steam_magnitude.append(0.0)
                continue
            
            # Encontrar maior mudança em janela curta
            max_change = 0.0
            for i in range(len(game_odds) - 1):
                change = abs(game_odds[i+1] - game_odds[i])
                if change > max_change:
                    max_change = change
            
            # Se mudança > 10%, considerar steam move
            is_steam = 1 if max_change > 0.10 else 0
            steam_detected.append(is_steam)
            steam_magnitude.append(max_change * 100)
        
        features["steam_move_detected"] = steam_detected
        features["steam_move_magnitude_pct"] = steam_magnitude
        
        return features
    
    def calculate_sharp_retail_features(
        self,
        odds_pinnacle: pd.Series,
        odds_other_bookmakers: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """
        Calcula proxies de sharp vs retail money.
        
        Lógica: Pinnacle é considerado o mercado "sharp". Se Pinnacle move
        mas outros bookmakers não seguem, é sinal de sharp money.
        
        Args:
            odds_pinnacle: Odds do Pinnacle (mercado sharp)
            odds_other_bookmakers: Dict de odds de outros bookmakers
            
        Returns:
            DataFrame com features sharp/retail
        """
        features = pd.DataFrame()
        
        for bookmaker, odds in odds_other_bookmakers.items():
            # Diferença entre Pinnacle e outros bookmakers
            features[f"odds_diff_pinnacle_{bookmaker}"] = (odds_pinnacle - odds).abs()
            
            # Se Pinnacle move mas outros não, é sharp
            # (proxy: se diferença > 5%, considerar divergência)
            features[f"sharp_divergence_{bookmaker}"] = (
                features[f"odds_diff_pinnacle_{bookmaker}"] > 0.05
            ).astype(int)
        
        # Número de bookmakers divergentes de Pinnacle
        divergence_cols = [col for col in features.columns if "sharp_divergence" in col]
        if divergence_cols:
            features["n_divergent_bookmakers"] = features[divergence_cols].sum(axis=1)
        
        return features
    
    def calculate_reversal_features(
        self,
        odds_history: List[List[float]]
    ) -> pd.DataFrame:
        """
        Detecta reversal patterns (odds mudam de direção).
        
        Exemplo: Odds sobem de 2.0 para 2.2, depois descem para 2.1.
        Isto pode indicar confusão no mercado ou late sharp action.
        
        Args:
            odds_history: Lista histórica de odds
            
        Returns:
            DataFrame com features de reversal
        """
        features = pd.DataFrame()
        
        if not odds_history or len(odds_history[0]) < 3:
            return features
        
        reversals_detected = []
        reversal_magnitude = []
        
        for game_odds in odds_history:
            if len(game_odds) < 3:
                reversals_detected.append(0)
                reversal_magnitude.append(0.0)
                continue
            
            # Detectar mudanças de direção
            n_reversals = 0
            max_magnitude = 0.0
            
            for i in range(len(game_odds) - 2):
                change1 = game_odds[i+1] - game_odds[i]
                change2 = game_odds[i+2] - game_odds[i+1]
                
                # Se sinais opostos, houve reversal
                if np.sign(change1) != np.sign(change2) and change1 != 0 and change2 != 0:
                    n_reversals += 1
                    magnitude = abs(change1) + abs(change2)
                    max_magnitude = max(max_magnitude, magnitude)
            
            reversals_detected.append(n_reversals)
            reversal_magnitude.append(max_magnitude * 100)
        
        features["n_reversals"] = reversals_detected
        features["reversal_magnitude_pct"] = reversal_magnitude
        features["has_reversal"] = (pd.Series(reversals_detected) > 0).astype(int)
        
        return features
    
    def calculate_volume_proxies(
        self,
        odds_open: pd.Series,
        odds_close: pd.Series,
        num_bettors_proxy: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calcula proxies de volume de apostas.
        
        Nota: Volume real não é público. Usamos proxies:
        - Magnitude do line movement (movimento maior = mais volume)
        - Número de reversals (volume + confusão)
        
        Args:
            odds_open: Odds de abertura
            odds_close: Odds de fecho
            num_bettors_proxy: Proxy de número de apostadores (se disponível)
            
        Returns:
            DataFrame com features de volume
        """
        features = pd.DataFrame()
        
        # Proxy 1: Magnitude do movimento = volume proxy
        features["volume_proxy_line_move"] = ((odds_close - odds_open).abs() / odds_open) * 100
        
        # Proxy 2: Se odds mudaram significativamente, há volume
        features["high_volume_indicator"] = (features["volume_proxy_line_move"] > 10).astype(int)
        
        # Se temos proxy de número de apostadores
        if num_bettors_proxy is not None:
            features["num_bettors_proxy"] = num_bettors_proxy
            features["high_interest_indicator"] = (num_bettors_proxy > num_bettors_proxy.median()).astype(int)
        
        return features
    
    def calculate_all_market_features(
        self,
        df: pd.DataFrame,
        odds_open_col: str = "open_odd_home",
        odds_close_col: str = "odd_1",
        odds_current_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calcula todas as features de mercado para um DataFrame.
        
        Args:
            df: DataFrame com dados de odds
            odds_open_col: Coluna de odds de abertura
            odds_close_col: Coluna de odds de fecho
            odds_current_col: Coluna de odds atuais (opcional)
            
        Returns:
            DataFrame com features adicionadas
        """
        if odds_open_col not in df.columns or odds_close_col not in df.columns:
            self.logger.warning(f"Colunas {odds_open_col} ou {odds_close_col} não encontradas")
            return df
        
        df_features = df.copy()
        
        # Line movement features
        line_features = self.calculate_line_movement_features(
            df[odds_open_col],
            df[odds_close_col],
            df[odds_current_col] if odds_current_col and odds_current_col in df.columns else None
        )
        
        for col in line_features.columns:
            df_features[col] = line_features[col].values
        
        # Adicionar features para away team também se existirem
        away_open = odds_open_col.replace("home", "away").replace("_home", "_away")
        away_close = odds_close_col.replace("_home", "_away").replace("1", "2")
        
        if away_open in df.columns and away_close in df.columns:
            line_features_away = self.calculate_line_movement_features(
                df[away_open],
                df[away_close],
                df[odds_current_col.replace("home", "away")] if odds_current_col and odds_current_col.replace("home", "away") in df.columns else None
            )
            
            for col in line_features_away.columns:
                df_features[col.replace("_home", "_away")] = line_features_away[col].values
        
        self.logger.info(f"Adicionadas {len(line_features.columns)} features de line movement")
        
        return df_features


def generate_synthetic_market_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Gera dados sintéticos com features de mercado para teste.
    """
    np.random.seed(42)
    
    data = []
    
    for i in range(n_samples):
        # Gerar odds de abertura
        open_home = np.random.uniform(1.5, 4.0)
        open_draw = open_home * np.random.uniform(1.1, 1.3)
        open_away = np.random.uniform(1.5, 4.0)
        
        # Simular line movement (alguns jogos com movimento significativo)
        if np.random.random() < 0.3:  # 30% dos jogos com movimento
            move_factor = np.random.uniform(0.9, 1.1)
            close_home = open_home * move_factor
        else:
            close_home = open_home * np.random.uniform(0.98, 1.02)
        
        close_draw = close_home * np.random.uniform(1.1, 1.3)
        close_away = open_away * np.random.uniform(0.98, 1.02)
        
        data.append({
            "match_id": f"match_{i}",
            "open_odd_home": round(open_home, 2),
            "odd_1": round(close_home, 2),
            "open_odd_draw": round(open_draw, 2),
            "odd_X": round(close_draw, 2),
            "open_odd_away": round(open_away, 2),
            "odd_2": round(close_away, 2),
            "home_team": f"Team_{np.random.randint(1, 50)}",
            "away_team": f"Team_{np.random.randint(1, 50)}",
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Teste
    market_features = MarketFeatures()
    
    # Gerar dados sintéticos
    df = generate_synthetic_market_data(100)
    
    # Calcular features
    df_with_features = market_features.calculate_all_market_features(
        df,
        odds_open_col="open_odd_home",
        odds_close_col="odd_1"
    )
    
    print("DataFrame com features de mercado:")
    print(df_with_features.head())
    print("\nColunas adicionadas:")
    print([col for col in df_with_features.columns if col not in df.columns])
