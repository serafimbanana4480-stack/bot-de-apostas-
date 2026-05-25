from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from scripts.ingest_nba_data import ingest_seasons
from src.database.connection import Base
from src.database.models import RawGame


@pytest.fixture(scope="function")
def db_session():
    """Sets up an in-memory SQLite database mimicking PostgreSQL schemas."""
    engine = create_engine("sqlite:///:memory:")
    
    with engine.connect() as conn:
        conn.execute(text("ATTACH DATABASE ':memory:' AS bronze;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS silver;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS gold;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS meta;"))
        conn.commit()

    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

@patch("scripts.ingest_nba_data.NBAIngestionClient")
@patch("scripts.ingest_nba_data.SessionLocal")
def test_ingestion_pipeline(mock_session_local, mock_client_class, db_session):
    """
    Test the ingestion process with mocked API responses and a database.
    """
    # Configure DB session mock
    mock_session_local.return_value = db_session
    
    # Configure NBA API Client mock
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock games data
    mock_client.fetch_games_for_season.side_effect = lambda season, type_: [
        {
            "GAME_ID": "0022300001",
            "SEASON": season,
            "GAME_DATE": "2023-10-24",
            "MATCHUP": "DEN vs. LAL",
            "TEAM_ABBREVIATION": "DEN"
        },
        {
            "GAME_ID": "0022300001",
            "SEASON": season,
            "GAME_DATE": "2023-10-24",
            "MATCHUP": "LAL @ DEN",
            "TEAM_ABBREVIATION": "LAL"
        }
    ] if type_ == "Regular Season" else []

    # Run ingestion
    ingest_seasons(["2023-24"], limit=5, dry_run=False)

    # Check results in the database
    games = db_session.query(RawGame).all()
    assert len(games) == 1
    
    game = games[0]
    assert game.game_id == "0022300001"
    assert game.home_team == "DEN"
    assert game.away_team == "LAL"
    assert game.season == "2023-24"
    assert game.game_date == date(2023, 10, 24)

@patch("scripts.verify_data_quality.SessionLocal")
def test_data_quality_checks_passed(mock_session_local, db_session):
    """
    Test verify_data_quality.py logic under PASSED condition.
    """
    mock_session_local.return_value = db_session
    
    # Add a mock game
    game = RawGame(
        game_id="0022300001",
        season="2023-24",
        game_date=date(2023, 10, 24),
        home_team="DEN",
        away_team="LAL",
        status="Final",
        raw_data={
            "game_details": [{"PTS": 110}],
            "ingestion_metadata": {"matchup": "DEN vs. LAL"}
        }
    )
    db_session.add(game)
    db_session.commit()
    
    from scripts.verify_data_quality import run_data_quality_checks
    
    # Executing this should complete without raising SystemExit or errors
    # If it fails, it calls sys.exit(1), but since it passes it should exit(0) or complete.
    with pytest.raises(SystemExit) as excinfo:
        run_data_quality_checks()
    assert excinfo.value.code == 0

