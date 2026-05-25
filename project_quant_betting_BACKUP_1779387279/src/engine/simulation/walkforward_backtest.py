"""
Walk-Forward Backtester Module.
Implements purged walk-forward cross-validation with embargo periods to prevent temporal leakage.
"""
import logging
from typing import Dict, Any, List, Generator, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class PurgedWalkForwardBacktest:
    """Walk-forward backtesting with purging and embargo."""
    
    def __init__(self, train_days: int = 180, test_days: int = 30, embargo_days: int = 7):
        self.train_days = train_days
        self.test_days = test_days
        self.embargo_days = embargo_days
        
    def generate_splits(self, dates: pd.Series) -> Generator[Tuple[pd.Series, pd.Series], None, None]:
        """
        Generate train/test boolean masks for each split.
        Applies embargo period between train and test.
        """
        dates = pd.to_datetime(dates)
        unique_dates = np.sort(dates.dt.date.unique())
        
        if len(unique_dates) < self.train_days + self.test_days:
            logger.warning("Not enough data for even one full walk-forward split.")
            return
            
        start_idx = 0
        while True:
            # Calculate temporal bounds
            train_start = unique_dates[start_idx]
            train_end = train_start + pd.Timedelta(days=self.train_days)
            
            test_start = train_end + pd.Timedelta(days=self.embargo_days) # Embargo applied here
            test_end = test_start + pd.Timedelta(days=self.test_days)
            
            if test_end > unique_dates[-1]:
                break # We've reached the end of the dataset
                
            # Create masks
            train_mask = (dates.dt.date >= train_start) & (dates.dt.date < train_end)
            test_mask = (dates.dt.date >= test_start) & (dates.dt.date < test_end)
            
            yield train_mask, test_mask
            
            # Step forward by the test period length
            # To step forward, we need to find the index in unique_dates corresponding to start_idx + test_days
            # Approximation for loop logic:
            advanced = False
            for i in range(start_idx, len(unique_dates)):
                if (unique_dates[i] - unique_dates[start_idx]).days >= self.test_days:
                    start_idx = i
                    advanced = True
                    break
            
            if not advanced:
                break
                
    def evaluate_split(self, y_true: pd.Series, y_prob: pd.Series, odds: pd.Series, stakes: pd.Series) -> Dict[str, float]:
        """Evaluate a single test split."""
        # Calculate returns
        implied_probs = 1.0 / odds
        edge = y_prob - implied_probs
        
        # Only evaluate bets actually placed (stake > 0)
        bet_mask = stakes > 0
        if not bet_mask.any():
            return {"roi": 0.0, "bets": 0, "win_rate": 0.0}
            
        y_bet = y_true[bet_mask]
        odds_bet = odds[bet_mask]
        stakes_bet = stakes[bet_mask]
        
        # Calculate PnL
        wins = y_bet == 1
        pnl = np.where(wins, stakes_bet * (odds_bet - 1), -stakes_bet)
        
        total_staked = stakes_bet.sum()
        total_pnl = pnl.sum()
        
        return {
            "roi": float(total_pnl / total_staked) * 100 if total_staked > 0 else 0.0,
            "bets": int(len(y_bet)),
            "win_rate": float(wins.mean()) * 100 if len(wins) > 0 else 0.0,
            "profit": float(total_pnl)
        }
