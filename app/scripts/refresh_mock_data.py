#!/usr/bin/env python3
"""Regenerate mock football data with open vs closing odds."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.local_store import LocalDataStore
from src.ingestion.mock_football_data import ensure_mock_dataset

if __name__ == "__main__":
    data_dir = os.getenv("DATA_DIR", "data")
    df = ensure_mock_dataset(data_dir, force=True)
    store = LocalDataStore(data_dir)
    store.save_matches(df, "football_mock")
    store.save_matches(df, "football_backtest")
    print(f"OK: {len(df)} matches | open/close cols | line_movement_home mean={df['line_movement_home'].mean():.4f}")
