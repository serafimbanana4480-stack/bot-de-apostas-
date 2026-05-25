from __future__ import annotations

import pandas as pd

from scripts.ingest_free_data import ingest_football_mock
from scripts.run_clv_report import ensure_data
from scripts.train_bot import load_football_df
from src.data.local_store import LocalDataStore
from src.simulation.historical_simulator import HonestHistoricalSimulator


def _mock_match_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 1,
                "date": "2024-01-01",
                "home_team": "A",
                "away_team": "B",
                "home_goals": 2,
                "away_goals": 1,
                "actual_outcome": "1",
                "league": "MOCK",
                "open_odd_home": 2.1,
                "open_odd_draw": 3.2,
                "open_odd_away": 3.5,
                "odd_1": 2.0,
                "odd_X": 3.1,
                "odd_2": 3.4,
                "pin_close_home": 1.95,
                "pin_close_draw": 3.0,
                "pin_close_away": 3.2,
                "line_movement_home": -0.0714,
                "closing_odd": 1.95,
            }
        ]
    )


def test_ingest_mock_writes_compatibility_aliases(tmp_path, monkeypatch):
    store = LocalDataStore(tmp_path)
    monkeypatch.setattr("scripts.ingest_free_data.ensure_mock_dataset", lambda *_args, **_kwargs: _mock_match_frame())

    count = ingest_football_mock(store)

    assert count == 1
    assert (tmp_path / "bronze" / "matches_football_mock.parquet").exists()
    assert (tmp_path / "bronze" / "matches_football_backtest.parquet").exists()


def test_train_bot_mock_source_loads_zero_cost_data(tmp_path):
    store = LocalDataStore(tmp_path)
    frame = _mock_match_frame()
    store.save_matches(frame, "football_mock")

    loaded = load_football_df(store, "mock")

    assert not loaded.empty
    assert loaded.iloc[0]["home_team"] == "A"


def test_clv_report_mock_source_prefers_football_mock_alias(tmp_path):
    store = LocalDataStore(tmp_path)
    frame = _mock_match_frame()
    store.save_matches(frame, "football_mock")

    loaded = ensure_data(store, "mock")

    assert not loaded.empty
    assert loaded.iloc[0]["away_team"] == "B"


def test_train_bot_real_odds_source_loads_football_real_odds(tmp_path):
    store = LocalDataStore(tmp_path)
    frame = _mock_match_frame().assign(home_team="REAL")
    store.save_matches(frame, "football_real_odds")

    loaded = load_football_df(store, "football_real_odds")

    assert not loaded.empty
    assert loaded.iloc[0]["home_team"] == "REAL"


def test_historical_simulator_prefers_real_odds_over_backtest(tmp_path):
    store = LocalDataStore(tmp_path)
    backtest = _mock_match_frame().assign(home_team="BACK")
    real_odds = _mock_match_frame().assign(home_team="REAL")
    store.save_matches(backtest, "football_backtest")
    store.save_matches(real_odds, "football_real_odds")

    simulator = HonestHistoricalSimulator(data_dir=str(tmp_path))
    loaded = simulator._load_football_history()

    assert not loaded.empty
    assert loaded.iloc[0]["home_team"] == "REAL"
