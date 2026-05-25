"""Tests for zero-cost local store and leakage detector."""
import pandas as pd
import pytest

from src.data.local_store import LocalDataStore
from src.validation.leakage_detector import LeakageDetector, check_odds_leakage


@pytest.fixture
def sample_matches():
    return pd.DataFrame({
        "match_id": [1, 2, 3],
        "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
        "home_team": ["A", "B", "C"],
        "away_team": ["B", "C", "A"],
        "home_goals": [2, 1, 0],
        "away_goals": [1, 1, 2],
        "actual_outcome": ["1", "X", "2"],
        "odd_1": [2.0, 2.1, 1.9],
    })


def test_local_store_roundtrip(tmp_path, sample_matches):
    store = LocalDataStore(tmp_path)
    store.save_matches(sample_matches, "test")
    loaded = store.load_matches("test")
    assert len(loaded) == 3
    report = store.save_report({"roi": 0.05}, "test_report")
    assert report.exists()
    assert store.load_report("test_report")["roi"] == 0.05


def test_leakage_detector_ordering(sample_matches):
    det = LeakageDetector()
    assert det.check_temporal_ordering(sample_matches, "date") is True
    reversed_df = sample_matches.sort_values("date", ascending=False).reset_index(drop=True)
    assert det.check_temporal_ordering(reversed_df, "date") is False


def test_leakage_enforce_raises_on_unsorted():
    import pandas as pd

    from src.validation.leakage_detector import LeakageError
    det = LeakageDetector()
    reversed_df = pd.DataFrame({
        "match_id": [1, 2, 3],
        "date": pd.to_datetime(["2024-03-01", "2024-02-01", "2024-01-01"]),
        "home_team": ["A", "B", "C"],
        "away_team": ["B", "C", "A"],
        "home_goals": [2, 1, 0],
        "away_goals": [1, 1, 2],
        "actual_outcome": ["1", "X", "2"],
        "odd_1": [2.0, 2.1, 1.9],
    })
    with pytest.raises(LeakageError):
        det.enforce_or_raise(reversed_df, time_col="date", target_col="actual_outcome")


def test_leakage_validate_training_frame(sample_matches):
    det = LeakageDetector()
    result = det.validate_training_frame(sample_matches, "date", "actual_outcome")
    assert result["row_count"] == 3
    assert result["temporal_order_ok"] is True


def test_check_odds_leakage_alias_falls_back_to_real_dataset(tmp_path, sample_matches):
    store = LocalDataStore(tmp_path)
    store.save_matches(sample_matches, "football_fdo")

    result = check_odds_leakage(tmp_path / "bronze" / "matches_football.parquet")

    assert result["passed"] is True
    assert result["odds_suspicious_columns"] == []
    assert result["file"].endswith("matches_football_fdo.parquet")


def test_check_odds_leakage_flags_closing_odds(tmp_path, sample_matches):
    store = LocalDataStore(tmp_path)
    sample_matches = sample_matches.assign(pin_close_home=[1.95, 2.05, 1.88])
    store.save_matches(sample_matches, "football_fdo")

    result = check_odds_leakage(tmp_path / "bronze" / "matches_football_fdo.parquet")

    assert result["passed"] is False
    assert "pin_close_home" in result["odds_suspicious_columns"]
