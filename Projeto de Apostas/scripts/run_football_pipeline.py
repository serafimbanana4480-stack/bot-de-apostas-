import logging
import os
import sys

import pandas as pd

# Ensure src modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.backtesting.historical_simulator import HistoricalSimulator
from src.ingestion.mock_football_data import generate_mock_football_data
from src.ml.models.football_poisson import FootballPoissonModel
from src.risk.portfolio_optimizer import PortfolioOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline():
    logger.info("--- PASSO 1: Ingestão de Dados Históricos ---")
    data_path = os.path.join("data", "mock_football.csv")
    
    if not os.path.exists(data_path):
        os.makedirs("data", exist_ok=True)
        df_matches = generate_mock_football_data(num_seasons=5)
        df_matches.to_csv(data_path, index=False)
    else:
        df_matches = pd.read_csv(data_path)
    
    df_matches['date'] = pd.to_datetime(df_matches['date'])
    logger.info(f"Carregados {len(df_matches)} jogos históricos.")
    
    logger.info("--- PASSO 2: Treino do Modelo (Walk-Forward validation simplificada) ---")
    # Para o PoC, vamos treinar o modelo com os primeiros 3 anos, e testar nos últimos 2 anos.
    train_end_date = df_matches['date'].min() + pd.DateOffset(years=3)
    
    df_train = df_matches[df_matches['date'] <= train_end_date].copy()
    df_test = df_matches[df_matches['date'] > train_end_date].copy()
    
    model = FootballPoissonModel()
    model.fit(df_train)
    logger.info("Modelo de Poisson treinado com dados de 3 épocas.")
    
    logger.info("--- PASSO 3: Geração de Previsões e Identificação de Valor ---")
    predictions = []
    opportunities = []
    
    for _, row in df_test.iterrows():
        probs = model.predict_match_outcome(row['home_team'], row['away_team'])
        
        # Encontrar a melhor odd de valor
        best_edge = -999
        best_outcome = None
        best_prob = 0
        best_odd = 0
        
        # Verificar edge para '1' (Vitória Casa)
        edge_1 = (probs['1'] * row['odd_1']) - 1
        if edge_1 > best_edge:
            best_edge, best_outcome, best_prob, best_odd = edge_1, '1', probs['1'], row['odd_1']
            
        # Verificar edge para 'X' (Empate)
        edge_X = (probs['X'] * row['odd_X']) - 1
        if edge_X > best_edge:
            best_edge, best_outcome, best_prob, best_odd = edge_X, 'X', probs['X'], row['odd_X']
            
        # Verificar edge para '2' (Vitória Fora)
        edge_2 = (probs['2'] * row['odd_2']) - 1
        if edge_2 > best_edge:
            best_edge, best_outcome, best_prob, best_odd = edge_2, '2', probs['2'], row['odd_2']
            
        predictions.append({
            "match_id": row['match_id'],
            "predicted_prob": best_prob,
            "predicted_outcome": best_outcome
        })
        
        if best_edge > 0.03: # Edge mínimo de 3% para considerar oportunidade
            opportunities.append({
                "match_id": row['match_id'],
                "prob": best_prob,
                "odd": best_odd,
                "predicted_outcome": best_outcome
            })
            
    df_predictions = pd.DataFrame(predictions)
    df_opportunities = pd.DataFrame(opportunities)
    
    logger.info("--- PASSO 4: Optimização de Portfólio (Riscos) ---")
    optimizer = PortfolioOptimizer()
    df_selected_bets = optimizer.get_optimal_portfolio(df_opportunities, max_bets=5000) 
    # Em produção max_bets seria por dia, aqui passamos todos para o simulador
    
    logger.info("--- PASSO 5: Simulação de Backtesting com Flat Staking ---")
    simulator = HistoricalSimulator()
    
    # df_results needs: match_id, actual_outcome, closing_odd
    # We map the closing odd based on the actual outcome
    df_results = df_test[['match_id', 'actual_outcome', 'closing_odd']].copy()
    
    # Vamos apenas simular as apostas que o otimizador aprovou
    df_predictions_to_simulate = df_predictions[df_predictions['match_id'].isin(df_selected_bets['match_id'])]
    
    results = simulator.run_simulation(df_predictions_to_simulate, df_results)
    
    print("\n" + "="*50)
    print("RELATÓRIO FINAL DA PROVA DE CONCEITO (FUTEBOL)")
    print("="*50)
    print(f"Total de Apostas Efetuadas: {results['total_bets']}")
    print(f"Taxa de Acerto (Win Rate): {results['win_rate']:.1%}")
    print(f"Lucro Total (Unidades): {results['total_profit_units']:.2f} U")
    print(f"ROI Global: {results['roi']:.2%}")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()
