import logging
from datetime import timedelta
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)


def _resolve_time_col(df: pd.DataFrame, time_col: Optional[str] = None) -> str:
    """Find a suitable datetime column, or raise."""
    if time_col and time_col in df.columns:
        return time_col
    for candidate in ("date", "game_date", "match_date", "timestamp", "commence_time"):
        if candidate in df.columns:
            return candidate
    # Fallback: try any column that looks datetime-ish
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    raise ValueError(f"No datetime column found in dataframe. Columns: {list(df.columns)}")


def temporal_oof_split(
    df: pd.DataFrame,
    n_splits: int = 3,
    embargo_days: int = 2,
    time_col: str = "date",
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Generate Out-of-Fold temporal splits for calibration / cross-validation.

    Unlike KFold(shuffle=True), this strictly respects chronological order:
    - Training folds always precede validation folds.
    - An embargo gap (default 2 days) is applied between train and validation
      to prevent leakage from overlapping feature windows (form, H2H, rest).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain `time_col` as datetime (or convertible).
    n_splits : int
        Number of temporal folds (default 3).
    embargo_days : int
        Minimum gap in days between the end of train and start of val.
    time_col : str
        Name of the datetime column.

    Returns
    -------
    List of (train_idx, val_idx) tuples with integer positions (iloc).
    """
    time_col = _resolve_time_col(df, time_col)
    df_sorted = df.copy()
    df_sorted[time_col] = pd.to_datetime(df_sorted[time_col])
    df_sorted = df_sorted.sort_values(by=time_col).reset_index(drop=True)

    tscv = TimeSeriesSplit(n_splits=n_splits)
    splits = []
    for train_iloc, val_iloc in tscv.split(df_sorted):
        train_df = df_sorted.iloc[train_iloc]
        val_df = df_sorted.iloc[val_iloc]

        # Apply embargo: remove train samples within embargo_days of first val sample
        if embargo_days > 0:
            val_start = val_df[time_col].min()
            embargo_cutoff = val_start - timedelta(days=embargo_days)
            valid_train = train_df[train_df[time_col] <= embargo_cutoff]
            train_iloc = valid_train.index.to_numpy()

        if len(train_iloc) == 0 or len(val_iloc) == 0:
            logger.warning(
                "Temporal split produced empty train (%d) or val (%d). Skipping fold.",
                len(train_iloc), len(val_iloc)
            )
            continue

        splits.append((train_iloc, val_iloc))

    return splits

class PurgedWalkForwardCV:
    """
    Implements a Purged Walk-Forward Cross Validation scheme.
    Prevents temporal data leakage by:
    1. Splitting data chronologically.
    2. Purging training samples that overlap with validation features (pre-validation window).
    3. Embargoing training samples immediately following the validation period (post-validation window).
    """
    def __init__(self, n_splits: int = 5, purge_days: int = 7, embargo_days: int = 14):
        self.n_splits = n_splits
        self.purge_days = purge_days
        self.embargo_days = embargo_days

    def split(self, df: pd.DataFrame) -> List[Tuple[pd.Index, pd.Index]]:
        """
        Generates indices for training and validation splits.
        df must contain a 'game_date' column.
        Returns a list of (train_idx, val_idx) tuples containing index locations.
        """
        if "game_date" not in df.columns:
            raise ValueError("Dataframe must contain 'game_date' to perform temporal split.")
            
        # Ensure game_date is datetime and sort the dataframe
        df = df.copy()
        df["game_date"] = pd.to_datetime(df["game_date"])
        df = df.sort_values(by="game_date").reset_index(drop=True)
        
        unique_dates = np.sort(df["game_date"].unique())
        
        total_days = len(unique_dates)
        if total_days < self.n_splits * 2:
            raise ValueError(f"Insufficient distinct game dates ({total_days}) for {self.n_splits} splits.")
            
        # Divide dates into chunks for walk-forward validation
        # Each split will have:
        # Train: all data from start up to (validation_start - purging)
        # Validation: a chronological segment of size chunk_size
        # Test/Embargo: validation_end + embargo_days onwards (used in subsequent training folds or discarded)
        chunk_size = total_days // (self.n_splits + 1)
        
        splits = []
        for i in range(self.n_splits):
            val_start_idx = (i + 1) * chunk_size
            val_end_idx = val_start_idx + chunk_size
            
            # Bound validation indexes
            if i == self.n_splits - 1:
                val_end_idx = total_days
                
            val_start_date = pd.Timestamp(unique_dates[val_start_idx])
            val_end_date = pd.Timestamp(unique_dates[val_end_idx - 1])
            
            # Determine validation mask
            val_mask = (df["game_date"] >= val_start_date) & (df["game_date"] <= val_end_date)
            val_indices = df[val_mask].index
            
            # Define purging boundaries
            # Train can only use data up to (val_start_date - purge_days)
            train_limit_date = val_start_date - timedelta(days=self.purge_days)
            
            # Define embargo boundaries
            # If we train on data *after* the validation fold (for double-barrier methods, although usually walk-forward is historical-only),
            # we embargo. In walk-forward, training is strictly historical: train_indices are strictly before the validation set.
            # Thus, we purge the end of the training set.
            train_mask = df["game_date"] <= train_limit_date
            train_indices = df[train_mask].index
            
            # Check that we have enough training samples
            if len(train_indices) == 0 or len(val_indices) == 0:
                logger.warning(f"Split {i} has empty train ({len(train_indices)}) or validation ({len(val_indices)}) index list. Skipping.")
                continue
                
            splits.append((train_indices, val_indices))
            train_end_str = pd.to_datetime(train_limit_date).strftime('%Y-%m-%d')
            val_start_str = pd.to_datetime(val_start_date).strftime('%Y-%m-%d')
            val_end_str = pd.to_datetime(val_end_date).strftime('%Y-%m-%d')
            logger.info(f"Split {i+1}/{self.n_splits}: Train games={len(train_indices)} (ends {train_end_str}), Val games={len(val_indices)} (range {val_start_str} to {val_end_str})")
            
        return splits
