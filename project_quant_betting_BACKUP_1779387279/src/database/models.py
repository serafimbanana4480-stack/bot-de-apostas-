"""
Database Models Module.
Defines SQLAlchemy 2.0 async models for the betting system.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(String, primary_key=True)
    sport = Column(String, nullable=False, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    kickoff_time = Column(DateTime, nullable=False, index=True)
    status = Column(String, default="SCHEDULED")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    predictions = relationship("Prediction", back_populates="match")
    bets = relationship("Bet", back_populates="match")
    odds = relationship("OddsHistory", back_populates="match")


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, index=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    market = Column(String, nullable=False)  # e.g., '1X2', 'MONEYLINE'
    selection = Column(String, nullable=False)  # e.g., 'HOME', 'AWAY'
    probability = Column(Float, nullable=False)
    edge = Column(Float, nullable=False)
    decision = Column(String, nullable=False)  # 'BET_NOW', 'WAIT', 'NO_BET'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    match = relationship("Match", back_populates="predictions")
    model_version = relationship("ModelVersion")


class Bet(Base):
    __tablename__ = "bets"
    
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    prediction_id = Column(String, ForeignKey("predictions.id"), nullable=True)
    bookmaker = Column(String, nullable=False)
    market = Column(String, nullable=False)
    selection = Column(String, nullable=False)
    odds = Column(Float, nullable=False)
    stake = Column(Float, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, PLACED, SETTLED, VOID
    settlement_status = Column(String, nullable=True)  # WON, LOST, PUSH
    pnl = Column(Float, nullable=True)
    closing_odds = Column(Float, nullable=True)
    clv_percentage = Column(Float, nullable=True)
    placed_at = Column(DateTime, default=datetime.utcnow, index=True)
    settled_at = Column(DateTime, nullable=True)
    
    match = relationship("Match", back_populates="bets")


class BankrollSnapshot(Base):
    __tablename__ = "bankroll_snapshots"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    in_play_balance = Column(Float, nullable=False)
    currency = Column(String, default="EUR")


class FeatureRecord(Base):
    __tablename__ = "feature_records"
    
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, index=True)
    feature_hash = Column(String, nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(String, primary_key=True)
    sport = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    version_tag = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OddsHistory(Base):
    __tablename__ = "odds_history"
    
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, index=True)
    bookmaker = Column(String, nullable=False)
    market = Column(String, nullable=False)
    selection = Column(String, nullable=False)
    odds = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    match = relationship("Match", back_populates="odds")


class SettlementRecord(Base):
    __tablename__ = "settlement_records"
    
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, unique=True)
    sources_consensus = Column(JSON, nullable=False)
    home_score = Column(Integer, nullable=False)
    away_score = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    settled_at = Column(DateTime, default=datetime.utcnow)
