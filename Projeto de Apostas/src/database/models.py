from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.database.connection import Base

# Cross-dialect JSON column type that falls back to JSON on SQLite and JSONB on PostgreSQL
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")

# =====================================================================
# 1. BRONZE SCHEMA (Raw Ingestion Data)
# =====================================================================

class RawGame(Base):
    __tablename__ = "raw_games"
    __table_args__ = {"schema": "bronze"}

    game_id = Column(String(50), primary_key=True)
    season = Column(String(15), nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    home_team = Column(String(50), nullable=False)
    away_team = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    raw_data = Column(JSON_TYPE, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())


class RawOdds(Base):
    __tablename__ = "raw_odds"
    __table_args__ = {"schema": "bronze"}

    odd_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(50), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    market_type = Column(String(50), nullable=False, index=True)
    home_odds = Column(Numeric(10, 4), nullable=False)
    away_odds = Column(Numeric(10, 4), nullable=False)
    raw_data = Column(JSON_TYPE, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())


class RawPlayer(Base):
    __tablename__ = "raw_players"
    __table_args__ = {"schema": "bronze"}

    player_id = Column(String(50), primary_key=True)
    game_id = Column(String(50), nullable=False, index=True)
    team_id = Column(String(50), nullable=False)
    player_name = Column(String(100), nullable=False)
    raw_data = Column(JSON_TYPE, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================================
# 2. SILVER SCHEMA (Cleaned Data & Box Scores)
# =====================================================================

class CleanGame(Base):
    __tablename__ = "games_clean"
    __table_args__ = {"schema": "silver"}

    game_id = Column(String(50), primary_key=True)
    season = Column(String(15), nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    home_team = Column(String(50), nullable=False)
    away_team = Column(String(50), nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CleanOdds(Base):
    __tablename__ = "odds_clean"
    __table_args__ = {"schema": "silver"}

    odd_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(50), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    market_type = Column(String(50), nullable=False, index=True)
    home_odds = Column(Numeric(10, 4), nullable=False)
    away_odds = Column(Numeric(10, 4), nullable=False)
    implied_prob_home = Column(Numeric(6, 4), nullable=False)
    implied_prob_away = Column(Numeric(6, 4), nullable=False)
    overround = Column(Numeric(6, 4), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


class PlayerStat(Base):
    __tablename__ = "player_stats"
    __table_args__ = {"schema": "silver"}

    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(50), nullable=False, index=True)
    player_id = Column(String(50), nullable=False, index=True)
    team_id = Column(String(50), nullable=False)
    player_name = Column(String(100), nullable=False)
    points = Column(Integer, nullable=False)
    assists = Column(Integer, nullable=False)
    rebounds = Column(Integer, nullable=False)
    minutes = Column(String(10), nullable=False)
    fgm = Column(Integer, nullable=False)
    fga = Column(Integer, nullable=False)
    fg_pct = Column(Numeric(6, 4), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================================
# 3. GOLD SCHEMA (Features, Predictions & Signals)
# =====================================================================

class FeatureRow(Base):
    __tablename__ = "features"
    __table_args__ = {"schema": "gold"}

    game_id = Column(String(50), primary_key=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    target = Column(Integer, nullable=True) # 1 if home wins, 0 if away wins, null if not played yet
    features_data = Column(JSON_TYPE, nullable=False) # Stores the 80 features as key-value pairs


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {"schema": "gold"}

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(50), nullable=False, index=True)
    model_version = Column(String(30), nullable=False, index=True)
    predicted_prob_home = Column(Numeric(6, 4), nullable=False)
    predicted_prob_away = Column(Numeric(6, 4), nullable=False)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = {"schema": "gold"}

    signal_id = Column(String(50), primary_key=True)
    game_id = Column(String(50), nullable=False, index=True)
    predicted_prob = Column(Numeric(6, 4), nullable=False)
    bookmaker_odds = Column(Numeric(10, 4), nullable=False)
    expected_edge = Column(Numeric(8, 4), nullable=False)
    stake_size = Column(Numeric(10, 2), nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="pending", index=True) # pending, executed, cancelled, settled
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================================
# 4. META SCHEMA (Execution, Circuit Breakers & System Logs)
# =====================================================================

class ModelRun(Base):
    __tablename__ = "model_runs"
    __table_args__ = {"schema": "meta"}

    run_id = Column(String(50), primary_key=True)
    model_name = Column(String(50), nullable=False, index=True)
    model_version = Column(String(30), nullable=False, index=True)
    hyperparameters = Column(JSON_TYPE, nullable=False)
    metrics = Column(JSON_TYPE, nullable=False)
    run_date = Column(DateTime(timezone=True), server_default=func.now())


class SubscriberLimit(Base):
    __tablename__ = "subscriber_limits"
    __table_args__ = {"schema": "meta"}

    limit_id = Column(Integer, primary_key=True, autoincrement=True)
    tier_name = Column(String(30), nullable=False, unique=True)
    max_calls = Column(Integer, nullable=False)
    monthly_cost = Column(Numeric(10, 2), nullable=False)


class CircuitBreakerLog(Base):
    __tablename__ = "circuit_breaker_log"
    __table_args__ = {"schema": "meta"}

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_type = Column(String(50), nullable=False, index=True) # drawdown, loss_streak, database_latency, api_failure
    description = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False, default="active") # active, acknowledged, resolved
