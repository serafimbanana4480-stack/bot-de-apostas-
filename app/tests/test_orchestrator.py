"""Tests for PipelineOrchestrator and odds persistence."""
from datetime import date

import pytest

from src.ingestion.odds_ingestor import OddsIngestor
from src.ingestion.schema_validator import validate_odds_api_event
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.sport_strategy import FootballStrategy, get_sport_strategy


def test_validate_odds_api_event_parses_bookmakers():
    raw = {
        "id": "evt1",
        "commence_time": "2025-06-01T15:00:00Z",
        "home_team": "Team A",
        "away_team": "Team B",
        "bookmakers": [{
            "key": "pinnacle",
            "markets": [{
                "key": "h2h",
                "outcomes": [
                    {"name": "Team A", "price": 2.1},
                    {"name": "Team B", "price": 3.5},
                ],
            }],
        }],
    }
    recs = validate_odds_api_event(raw, "football")
    assert len(recs) == 1
    assert recs[0].bookmaker == "pinnacle"
    assert recs[0].is_pinnacle is True


def test_football_strategy_build_opportunities():
    strategy = FootballStrategy()
    opps = strategy.build_opportunities(date.today(), "live")
    assert isinstance(opps, list)


def test_orchestrator_run_daily_football():
    orch = PipelineOrchestrator("football", mode="live", strict_leakage=False)
    summary = orch.run_daily(date.today())
    assert summary["sport"] == "football"
    assert "ingest" in summary
    assert "decisions" in summary


def test_odds_ingestor_persist_roundtrip(tmp_path):
    ingestor = OddsIngestor(data_root=str(tmp_path))
    df = __import__("pandas").DataFrame([{
        "event_id": "e1",
        "sport": "football",
        "commence_time": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "bookmaker": "pinnacle",
        "market": "h2h",
        "odds_home": 2.0,
        "odds_away": 3.0,
        "odds_draw": None,
        "captured_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "is_pinnacle": True,
    }])
    ingestor._persist(df, "football", date.today())
    loaded = ingestor.load_history("football")
    assert len(loaded) >= 1


def test_get_sport_strategy_unknown():
    with pytest.raises(ValueError):
        get_sport_strategy("cricket")
