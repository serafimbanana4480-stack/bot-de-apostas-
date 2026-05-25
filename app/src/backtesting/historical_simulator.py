import logging

import numpy as np
import pandas as pd


class HistoricalSimulator:
    """
    Rigorous Backtesting Simulator.
    Evaluates predictions against true historical closing lines using a Flat Staking strategy.
    No "odd 2.0" assumptions. Uses real odds.
    """
    def __init__(self, stake_percentage: float = 0.01):
        self.logger = logging.getLogger(__name__)
        self.stake_percentage = stake_percentage
        self.results = []
        
    def calculate_edge(self, prob: float, odd: float) -> float:
        """Edge = P * Odd - 1"""
        return (prob * odd) - 1.0

    def run_simulation(self, df_predictions: pd.DataFrame, df_results: pd.DataFrame):
        """
        df_predictions needs: match_id, predicted_prob, predicted_outcome
        df_results needs: match_id, actual_outcome, closing_odd
        """
        self.logger.info("Starting historical walk-forward simulation...")
        
        # Merge predictions with actual results and odds
        df_merged = pd.merge(df_predictions, df_results, on=['match_id'])
        
        # Calculate edge for every prediction
        df_merged['estimated_edge'] = df_merged.apply(
            lambda row: self.calculate_edge(row['predicted_prob'], row['closing_odd']), 
            axis=1
        )
        
        # Filter only bets with positive edge > threshold (e.g. 2%)
        df_bets = df_merged[df_merged['estimated_edge'] > 0.02].copy()
        
        if df_bets.empty:
            return {"total_bets": 0, "roi": 0, "total_profit_units": 0, "win_rate": 0}
            
        # Calculate flat stake PnL
        df_bets['stake'] = 1.0 # 1 unit per bet
        df_bets['profit'] = np.where(
            df_bets['predicted_outcome'] == df_bets['actual_outcome'],
            (df_bets['closing_odd'] - 1) * df_bets['stake'],
            -df_bets['stake']
        )
        
        # Calculate aggregate metrics
        roi = df_bets['profit'].sum() / df_bets['stake'].sum()
        total_bets = len(df_bets)
        
        self.logger.info(f"Simulation Complete. Total Bets: {total_bets}, ROI: {roi:.2%}")
        
        return {
            "total_bets": total_bets,
            "roi": roi,
            "total_profit_units": df_bets['profit'].sum(),
            "win_rate": (df_bets['profit'] > 0).mean()
        }
