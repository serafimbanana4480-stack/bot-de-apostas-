from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from src.database.connection import Base, get_db
from src.database.models import Prediction, Signal


@pytest.fixture(scope="function")
def test_db():
    """Sets up an in-memory SQLite database mimicking PostgreSQL schemas using StaticPool."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # SQLite schema attachment simulation
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


@pytest.fixture(scope="function")
def client(test_db):
    """Overrides get_db dependency to point to the in-memory test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    """Test health check route."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_endpoint(client):
    """Test predict endpoint using fallback synthetic models."""
    payload = {
        "features": {
            "elo_diff": 15.0,
            "rest_diff": 1.0,
            "market_overround": 0.04,
            "odds_home": 1.95,
            "odds_away": 1.85,
            "win_rate_5_diff": 0.1
        },
        "odds_home": 1.95,
        "odds_away": 1.85
    }
    
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "calibrated_prob_home" in data
    assert "edge_home" in data
    assert "stake_pct" in data


def test_generate_signal_endpoint(client, test_db):
    """Test generating a signal from a predicted match and verifying persistence."""
    payload = {
        "game_id": "20261020-MIA-MIL",
        "features": {
            "elo_diff": 50.0,
            "rest_diff": 0.0,
            "market_overround": 0.04,
            "odds_home": 2.10,
            "odds_away": 1.75,
            "win_rate_5_diff": 0.2
        },
        "odds_home": 2.10,
        "odds_away": 1.75,
        "base_bankroll": 2000.0
    }

    # Temporarily mock send_signal_alert to avoid network tasks
    import src.telegram.bot
    original_send = src.telegram.bot.send_signal_alert
    
    async def mock_send(signal_data):
        return True
    
    src.telegram.bot.send_signal_alert = mock_send

    try:
        response = client.post("/api/v1/signals/generate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "prediction" in data
        assert "signal" in data
        
        # Verify db persistence
        db_pred = test_db.query(Prediction).filter_by(game_id="20261020-MIA-MIL").first()
        assert db_pred is not None
        
        db_sig = test_db.query(Signal).filter_by(game_id="20261020-MIA-MIL").first()
        # It could be none if no edge was detected, but prediction exists
        if db_sig:
            assert float(db_sig.stake_size) >= 0.0
    finally:
        src.telegram.bot.send_signal_alert = original_send


def test_get_signals_endpoint(client, test_db):
    """Test retrieving list of signals with filter support."""
    # Seed a fake signal
    sig = Signal(
        signal_id="SIG-TEST-01",
        game_id="TEST-GAME",
        predicted_prob=Decimal("0.6200"),
        bookmaker_odds=Decimal("1.8000"),
        expected_edge=Decimal("0.1160"),
        stake_size=Decimal("50.00"),
        approved=True,
        status="pending"
    )
    test_db.add(sig)
    test_db.commit()

    response = client.get("/api/v1/signals?status=pending")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 1
    assert data[0]["signal_id"] == "SIG-TEST-01"
    assert data[0]["status"] == "pending"
