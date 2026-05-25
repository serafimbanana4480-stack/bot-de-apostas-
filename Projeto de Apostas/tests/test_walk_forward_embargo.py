"""
Tests for WalkForwardValidator embargo and purging behaviour.
"""
import pandas as pd
import pytest

from src.validation.walk_forward import WalkForwardValidator


def _make_daily_df(start: str, periods: int) -> pd.DataFrame:
    dates = pd.date_range(start, periods=periods, freq="D")
    return pd.DataFrame({
        "date": dates,
        "value": range(periods),
    })


def test_walk_forward_respects_embargo():
    df = _make_daily_df("2023-01-01", 100)
    validator = WalkForwardValidator(
        train_window_days=30,
        test_window_days=10,
        embargo_days=5,
    )
    splits = validator.split_data(df, "date")
    assert len(splits) > 0

    for split in splits:
        train = split["train"]
        test = split["test"]
        train_max = train["date"].max()
        test_min = test["date"].min()
        gap_days = (test_min - train_max).days
        # Gap must be at least embargo_days (or more if natural gap exists)
        assert gap_days >= 5, f"Embargo violated: gap={gap_days}d < 5d"


def test_walk_forward_no_overlap():
    df = _make_daily_df("2023-01-01", 200)
    validator = WalkForwardValidator(
        train_window_days=60,
        test_window_days=20,
        embargo_days=2,
    )
    splits = validator.split_data(df, "date")
    for split in splits:
        train = split["train"]
        test = split["test"]
        assert train["date"].max() < test["date"].min()
        # No shared rows
        shared = set(train["date"]).intersection(set(test["date"]))
        assert len(shared) == 0, "Train and test overlap detected"
