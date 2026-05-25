from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base
from src.database.models import (
    CircuitBreakerLog,
    CleanGame,
    FeatureRow,
    ModelRun,
    Prediction,
    RawGame,
    Signal,
)


@pytest.fixture(scope="function")
def db_session():
    """Sets up an in-memory SQLite database mimicking PostgreSQL schemas."""
    engine = create_engine("sqlite:///:memory:")
    
    # SQLite schema attachment simulation
    with engine.connect() as conn:
        conn.execute(text("ATTACH DATABASE ':memory:' AS bronze;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS silver;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS gold;"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS meta;"))
        conn.commit()

    # Create tables
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_raw_game_model(db_session):
    """Test raw game ingestion model serialization."""
    game = RawGame(
        game_id="20261015-BOS-LAL",
        season="2025-26",
        game_date=date(2026, 10, 15),
        home_team="BOS",
        away_team="LAL",
        status="Final",
        raw_data={"box_score": {"home": 110, "away": 105}}
    )
    db_session.add(game)
    db_session.commit()

    fetched = db_session.query(RawGame).filter_by(game_id="20261015-BOS-LAL").first()
    assert fetched is not None
    assert fetched.season == "2025-26"
    assert fetched.raw_data["box_score"]["home"] == 110


def test_clean_game_and_features_model(db_session):
    """Test clean games and feature store relations."""
    game_clean = CleanGame(
        game_id="20261015-BOS-LAL",
        season="2025-26",
        game_date=date(2026, 10, 15),
        home_team="BOS",
        away_team="LAL",
        home_score=110,
        away_score=105,
        status="Final"
    )
    
    features = FeatureRow(
        game_id="20261015-BOS-LAL",
        target=1,
        features_data={"win_streak_home": 5, "win_streak_away": 2}
    )

    db_session.add(game_clean)
    db_session.add(features)
    db_session.commit()

    db_features = db_session.query(FeatureRow).filter_by(game_id="20261015-BOS-LAL").first()
    assert db_features is not None
    assert db_features.target == 1
    assert db_features.features_data["win_streak_home"] == 5


def test_signals_and_predictions_model(db_session):
    """Test expected predictions and Kelly betting signals."""
    prediction = Prediction(
        game_id="20261015-BOS-LAL",
        model_version="v4.0.0-xgb",
        predicted_prob_home=Decimal("0.5850"),
        predicted_prob_away=Decimal("0.4150")
    )
    
    signal = Signal(
        signal_id="SIG-20261015-001",
        game_id="20261015-BOS-LAL",
        predicted_prob=Decimal("0.5850"),
        bookmaker_odds=Decimal("1.8500"),
        expected_edge=Decimal("0.0822"), # (0.585 * 1.85) - 1 = 0.08225 (8.22%)
        stake_size=Decimal("25.00"),
        approved=True,
        status="pending"
    )

    db_session.add(prediction)
    db_session.add(signal)
    db_session.commit()

    db_signal = db_session.query(Signal).filter_by(signal_id="SIG-20261015-001").first()
    assert db_signal is not None
    assert db_signal.expected_edge == Decimal("0.0822")
    assert db_signal.approved is True


def test_circuit_breaker_and_model_run_meta(db_session):
    """Test circuit breaker system logging and model run metadata metadata."""
    run = ModelRun(
        run_id="run-001",
        model_name="xgboost_moneyline",
        model_version="v4.0.0-xgb",
        hyperparameters={"max_depth": 6, "lr": 0.05},
        metrics={"auc": 0.582, "brier": 0.221}
    )
    
    breaker = CircuitBreakerLog(
        trigger_type="drawdown",
        description="Daily drawdown reached 5.12% exceeding 5.0% threshold."
    )

    db_session.add(run)
    db_session.add(breaker)
    db_session.commit()

    db_breaker = db_session.query(CircuitBreakerLog).filter_by(trigger_type="drawdown").first()
    assert db_breaker is not None
    assert "drawdown" in db_breaker.description
    assert db_breaker.status == "active"
