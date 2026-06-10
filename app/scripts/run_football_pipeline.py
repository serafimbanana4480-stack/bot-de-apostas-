#!/usr/bin/env python3
"""
Football Pipeline — Real data only.

Uses historical data with real Pinnacle odds from football-data.co.uk.
NO MOCK DATA IS GENERATED.

Usage:
    py scripts/run_football_pipeline.py
"""
import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtesting.historical_simulator import HistoricalSimulator
from src.ingestion.real_data_pipeline import ensure_real_data_exists
from src.ml.models.football_poisson_v2 import FootballPoissonModelV2
from src.risk.portfolio_optimizer import PortfolioOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("--- STEP 1: Load Real Historical Data ---")
    data_path = ensure_real_data_exists("data/bronze")
    df_matches = pd.read_parquet(data_path)
    df_matches['date'] = pd.to_datetime(df_matches['date'])
    logger.info("Loaded %d real matches with Pinnacle odds.", len(df_matches))

    logger.info("--- STEP 2: Train Model (Walk-Forward) ---")
    train_end_date = df_matches['date'].min() + pd.DateOffset(years=3)

    df_train = df_matches[df_matches['date'] <= train_end_date].copy()
    df_test = df_matches[df_matches['date'] > train_end_date].copy()

    model = FootballPoissonModelV2(use_dixon_coles=True, reg_lambda=0.15, time_decay_halflife_days=60.0)
    model.fit(df_train, calibrate=True)
    logger.info("PoissonV2 trained on %d matches (%s to %s).", len(df_train), df_train['date'].min().date(), df_train['date'].max().date())

    logger.info("--- STEP 3: Generate Predictions & Edge Detection ---")
    predictions = []
    opportunities = []

    for _, row in df_test.iterrows():
        probs = model.predict_match_outcome(row['home_team'], row['away_team'], league=row.get('league'), apply_calibration=True)

        best_edge = -999
        best_outcome = None
        best_prob = 0
        best_odd = 0

        for outcome, odd_col in [('1', 'odd_1'), ('X', 'odd_X'), ('2', 'odd_2')]:
            odd = row.get(odd_col)
            if pd.isna(odd) or odd <= 1.0:
                continue
            edge = (probs[outcome] * odd) - 1
            if edge > best_edge:
                best_edge, best_outcome, best_prob, best_odd = edge, outcome, probs[outcome], odd

        predictions.append({
            "match_id": row['match_id'],
            "predicted_prob": best_prob,
            "predicted_outcome": best_outcome
        })

        if best_edge > 0.03:
            opportunities.append({
                "match_id": row['match_id'],
                "prob": best_prob,
                "odd": best_odd,
                "predicted_outcome": best_outcome
            })

    df_predictions = pd.DataFrame(predictions)
    df_opportunities = pd.DataFrame(opportunities)

    logger.info("--- STEP 4: Portfolio Optimization ---")
    optimizer = PortfolioOptimizer()
    df_selected_bets = optimizer.get_optimal_portfolio(df_opportunities, max_bets=5000)

    logger.info("--- STEP 5: Backtest Simulation ---")
    simulator = HistoricalSimulator()
    df_results = df_test[['match_id', 'actual_outcome', 'closing_odd']].copy()
    df_predictions_to_simulate = df_predictions[df_predictions['match_id'].isin(df_selected_bets['match_id'])]
    results = simulator.run_simulation(df_predictions_to_simulate, df_results)

    print("\n" + "="*50)
    print("FOOTBALL PIPELINE REPORT (REAL DATA ONLY)")
    print("="*50)
    print(f"Total Bets: {results['total_bets']}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"Profit (Units): {results['total_profit_units']:.2f} U")
    print(f"ROI: {results['roi']:.2%}")
    print("="*50)


if __name__ == "__main__":
    run_pipeline()
