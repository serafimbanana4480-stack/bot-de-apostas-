import logging
from datetime import timedelta
from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd


class WalkForwardValidator:
    """
    Implements Walk-Forward Validation for Time-Series Betting Models.
    Prevents Look-Ahead Bias by strictly separating training and testing temporal windows.
    Supports purging (removing overlapping training samples) and embargo (gap after train).
    """
    def __init__(self, train_window_days: int = 365 * 2, test_window_days: int = 30, embargo_days: int = 2):
        self.logger = logging.getLogger(__name__)
        self.train_window_days = train_window_days
        self.test_window_days = test_window_days
        self.embargo_days = embargo_days

    def split_data(self, df: pd.DataFrame, date_column: str) -> List[Dict[str, pd.DataFrame]]:
        """
        Creates temporal splits for walk-forward training/testing.
        Data MUST be sorted by date before passing to this function.
        """
        if not np.issubdtype(df[date_column].dtype, np.datetime64):
            df[date_column] = pd.to_datetime(df[date_column])
            
        df = df.sort_values(by=date_column).reset_index(drop=True)
        min_date = df[date_column].min()
        max_date = df[date_column].max()
        
        splits = []
        current_train_end = min_date + timedelta(days=self.train_window_days)
        
        while current_train_end < max_date:
            current_test_end = current_train_end + timedelta(days=self.test_window_days)
            
            # Train set: strictly BEFORE current_train_end, minus embargo gap
            train_cutoff = current_train_end - timedelta(days=self.embargo_days)
            train_mask = df[date_column] < train_cutoff
            train_set = df[train_mask]
            
            # Test set: >= current_train_end AND < current_test_end
            test_mask = (df[date_column] >= current_train_end) & (df[date_column] < current_test_end)
            test_set = df[test_mask]
            
            if not test_set.empty:
                splits.append({
                    "train": train_set,
                    "test": test_set,
                    "train_end": current_train_end,
                    "test_end": current_test_end
                })
                
            current_train_end = current_test_end
            
        return splits

    def run_backtest(
        self, 
        df: pd.DataFrame, 
        date_column: str,
        model_fit_func: Callable[[pd.DataFrame], Any],
        model_predict_func: Callable[[Any, pd.DataFrame], pd.DataFrame],
        evaluate_func: Callable[[pd.DataFrame], Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Runs the full walk-forward backtest loop.
        
        :param df: Historical dataset containing features and targets.
        :param date_column: The name of the datetime column.
        :param model_fit_func: A function that takes a training DataFrame and returns a fitted model.
        :param model_predict_func: A function that takes the fitted model and test DataFrame, 
                                   and returns the test DataFrame with predictions appended.
        :param evaluate_func: A function that evaluates the predictions (e.g. calculates ROI or CLV).
        """
        self.logger.info("Initializing Walk-Forward Backtest...")
        splits = self.split_data(df, date_column)
        
        if not splits:
            self.logger.warning("Not enough data to create walk-forward splits.")
            return {}
            
        self.logger.info(f"Generated {len(splits)} temporal folds.")
        
        all_test_predictions = []
        fold_metrics = []
        
        for idx, split in enumerate(splits):
            train_df = split["train"]
            test_df = split["test"]
            
            # Data leakage protection: Raise if test dates overlap train dates
            if train_df[date_column].max() >= test_df[date_column].min():
                raise ValueError(
                    "CRITICAL: Look-ahead bias detected! Train dates overlap test dates."
                )
                
            # 1. Fit Model
            fitted_model = model_fit_func(train_df)
            
            # 2. Predict
            test_preds = model_predict_func(fitted_model, test_df)
            all_test_predictions.append(test_preds)
            
            # 3. Evaluate Fold
            metrics = evaluate_func(test_preds)
            metrics["fold"] = idx + 1
            metrics["test_start"] = split["train_end"]
            metrics["test_end"] = split["test_end"]
            fold_metrics.append(metrics)
            
        # Combine all predictions
        combined_preds = pd.concat(all_test_predictions, ignore_index=True)
        
        # Overall evaluation
        overall_metrics = evaluate_func(combined_preds)
        
        return {
            "overall_metrics": overall_metrics,
            "fold_metrics": fold_metrics,
            "total_folds": len(splits),
            "combined_predictions": combined_preds
        }
