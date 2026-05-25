"""
Configuration Management — Pydantic v2 Settings.

Centralised configuration loaded from environment variables, .env files,
and optional YAML overrides.  All sections are grouped logically so that
downstream modules can depend on a single ``Settings`` instance.

Usage::

    from src.core.config import settings
    print(settings.database_url)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application-wide configuration validated from env vars / .env."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment selector.",
    )
    DEBUG: bool = Field(default=False)

    # ------------------------------------------------------------------
    # API Keys & Credentials
    # ------------------------------------------------------------------
    NBA_API_KEY: str = Field(default="")
    BETFAIR_APP_KEY: str = Field(default="")
    BETFAIR_USERNAME: str = Field(default="")
    BETFAIR_PASSWORD: SecretStr = Field(default="")
    BETFAIR_CERT_PATH: str = Field(default="")
    BETFAIR_KEY_PATH: str = Field(default="")
    TELEGRAM_BOT_TOKEN: SecretStr = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    ODDS_API_KEY: str = Field(default="")

    # ------------------------------------------------------------------
    # Database (PostgreSQL)
    # ------------------------------------------------------------------
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(default="postgres")
    DB_PASS: SecretStr = Field(default="postgres")
    DB_NAME: str = Field(default="vbq_unified")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_ECHO_SQL: bool = Field(default=False)

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy."""
        password = self.DB_PASS.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def database_url_sync(self) -> str:
        """Sync database URL (for Alembic migrations)."""
        password = self.DB_PASS.get_secret_value()
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ------------------------------------------------------------------
    # Redis Cache
    # ------------------------------------------------------------------
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: SecretStr = Field(default="")
    REDIS_DB: int = Field(default=0)
    REDIS_DEFAULT_TTL: int = Field(
        default=300,
        description="Default cache TTL in seconds.",
    )

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        password = self.REDIS_PASSWORD.get_secret_value()
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    EXECUTION_MODE: Literal["live", "paper", "backtest"] = Field(
        default="paper",
        description="Trade execution mode.",
    )
    MAX_CONCURRENT_BETS: int = Field(default=5)
    ORDER_TIMEOUT_SECONDS: int = Field(default=30)
    BETFAIR_COMMISSION_RATE: float = Field(default=0.05)

    # ------------------------------------------------------------------
    # Risk Limits
    # ------------------------------------------------------------------
    MAX_DAILY_LOSS_PCT: float = Field(default=5.0)
    KELLY_MULTIPLIER: float = Field(default=0.25)
    MAX_DRAWDOWN_PCT: float = Field(default=20.0)
    MAX_LOSS_STREAK: int = Field(default=5)
    MAX_VOLATILITY_THRESHOLD: float = Field(default=2.0)

    # ------------------------------------------------------------------
    # Monitoring & Observability
    # ------------------------------------------------------------------
    LOG_LEVEL: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = Field(default="INFO")
    LOG_FORMAT: Literal["json", "text"] = Field(default="json")
    LOG_FILE: str = Field(default="logs/app.log")
    SENTRY_DSN: str = Field(default="")
    METRICS_ENABLED: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)

    # ------------------------------------------------------------------
    # MLflow / Experiment tracking
    # ------------------------------------------------------------------
    MLFLOW_TRACKING_URI: str = Field(default="http://localhost:5000")
    MLFLOW_EXPERIMENT_NAME: str = Field(default="nba_value_betting")

    # ------------------------------------------------------------------
    # API Server
    # ------------------------------------------------------------------
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    JWT_SECRET_KEY: SecretStr = Field(default="change-me")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
    )
    RATE_LIMIT_ENABLED: bool = Field(default=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton ``Settings`` instance."""
    return Settings()


# Convenience alias — import ``settings`` directly.
settings: Settings = get_settings()
