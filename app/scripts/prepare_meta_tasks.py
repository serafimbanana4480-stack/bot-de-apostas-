#!/usr/bin/env python3
"""
Prepare meta-learning tasks from existing sport data.

Splits each sport's data into support/query sets for MAML training.
Each task represents a "sport" that the meta-learner should adapt to.

Usage:
    poetry run python scripts/prepare_meta_tasks.py --sports football,nba,ufc
    poetry run python scripts/prepare_meta_tasks.py --sports football,nba --support-size 10
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.data.local_store import LocalDataStore
from src.ml.meta.maml import MetaTask

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("prepare_meta_tasks")


def load_sport_data(sport: str) -> Optional[Any]:
    """Load data for a sport from Parquet store."""
    store = LocalDataStore(settings.DATA_DIR)
    try:
        df = store.load_parquet(f"{sport}_features")
        if df is not None and len(df) > 0:
            logger.info("Loaded %d rows for %s", len(df), sport)
            return df
    except Exception:
        pass

    # Try alternative naming
    try:
        df = store.load_parquet(f"{sport}_odds_history")
        if df is not None and len(df) > 0:
            logger.info("Loaded %d rows for %s (odds_history)", len(df), sport)
            return df
    except Exception:
        pass

    return None


def dataframe_to_arrays(df: Any, target_col: str = "actual_outcome") -> Tuple[np.ndarray, np.ndarray]:
    """Convert DataFrame to (X, y) numpy arrays."""
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            # Exclude non-feature columns
            exclude_cols = {target_col, "match_id", "date", "season", "closing_odd", "actual_outcome"}
            feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.float32, np.int64, np.int32)]
            X = df[feature_cols].values.astype(np.float32)
            y = df[target_col].values.astype(np.float32) if target_col in df.columns else np.ones(len(df)) * 0.5
            return X, y
    except ImportError:
        pass

    # Fallback: assume it's already numpy
    arr = np.asarray(df)
    X = arr[:, :-1].astype(np.float32)
    y = arr[:, -1].astype(np.float32)
    return X, y


def create_meta_task(
    sport: str,
    X: np.ndarray,
    y: np.ndarray,
    support_size: int = 10,
    n_query: int = 50,
    seed: int = 42,
) -> MetaTask:
    """Create a MetaTask from sport data with support/query split."""
    rng = np.random.RandomState(seed)
    n = len(X)

    if n < support_size + n_query:
        logger.warning(
            "Not enough data for %s (%d rows, need %d). Reducing query size.",
            sport, n, support_size + n_query,
        )
        n_query = max(10, n - support_size)

    # Shuffle
    indices = rng.permutation(n)
    support_idx = indices[:support_size]
    query_idx = indices[support_size:support_size + n_query]

    # Normalize features (zero mean, unit variance — computed on support set)
    X_mean = X[support_idx].mean(axis=0, keepdims=True)
    X_std = X[support_idx].std(axis=0, keepdims=True) + 1e-8

    X_support = (X[support_idx] - X_mean) / X_std
    X_query = (X[query_idx] - X_mean) / X_std
    y_support = y[support_idx]
    y_query = y[query_idx]

    return MetaTask(
        name=sport,
        X_support=X_support,
        y_support=y_support,
        X_query=X_query,
        y_query=y_query,
    )


def prepare_tasks(args: argparse.Namespace) -> None:
    """Main task preparation pipeline."""
    sports = [s.strip() for s in args.sports.split(",")]
    support_size = args.support_size
    n_query = args.query_size
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = []

    for sport in sports:
        logger.info("Processing sport: %s", sport)
        df = load_sport_data(sport)

        if df is None:
            logger.warning("No data found for %s — generating synthetic task", sport)
            X, y = generate_synthetic_task(sport, support_size + n_query + 100)
        else:
            X, y = dataframe_to_arrays(df)

        task = create_meta_task(sport, X, y, support_size, n_query, seed=42)
        tasks.append(task)
        logger.info(
            "Created task for %s: support=%d, query=%d, features=%d",
            sport, len(task.X_support), len(task.X_query), task.X_support.shape[1],
        )

    # Save tasks
    for task in tasks:
        path = output_dir / f"meta_task_{task.name}.npz"
        np.savez(
            path,
            X_support=task.X_support,
            y_support=task.y_support,
            X_query=task.X_query,
            y_query=task.y_query,
            name=task.name,
        )
        logger.info("Saved task to %s", path)

    logger.info("Prepared %d meta-learning tasks in %s", len(tasks), output_dir)


def generate_synthetic_task(sport: str, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data when real data is unavailable."""
    rng = np.random.RandomState(42)
    n_features = 30
    X = rng.randn(n_samples, n_features).astype(np.float32)
    # Create a non-trivial target function
    y = (X[:, 0] * 0.3 + X[:, 1] * 0.2 + rng.randn(n_samples) * 0.1 > 0).astype(np.float32)
    return X, y


def main():
    parser = argparse.ArgumentParser(description="Prepare meta-learning tasks")
    parser.add_argument("--sports", type=str, default="football,nba,ufc", help="Comma-separated sport names")
    parser.add_argument("--support-size", type=int, default=10, help="Support set size per task")
    parser.add_argument("--query-size", type=int, default=50, help="Query set size per task")
    parser.add_argument("--output-dir", type=str, default="data/meta_tasks", help="Output directory")
    args = parser.parse_args()
    prepare_tasks(args)


if __name__ == "__main__":
    main()
