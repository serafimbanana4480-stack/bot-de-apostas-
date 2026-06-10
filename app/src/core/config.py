"""
Configuration Management using Pydantic Settings.
Validates environment variables for the system.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys and Credentials
    NBA_API_KEY: str = Field(default="", validation_alias="NBA_API_KEY")
    BETFAIR_APP_KEY: str = Field(default="", validation_alias="BETFAIR_APP_KEY")
    BETFAIR_USERNAME: str = Field(default="", validation_alias="BETFAIR_USERNAME")
    BETFAIR_PASSWORD: str = Field(default="", validation_alias="BETFAIR_PASSWORD")
    BETFAIR_CERT_PATH: str = Field(default="", validation_alias="BETFAIR_CERT_PATH")
    BETFAIR_KEY_PATH: str = Field(default="", validation_alias="BETFAIR_KEY_PATH")
    BETFAIR_SANDBOX: bool = Field(default=True, validation_alias="BETFAIR_SANDBOX")
    BETFAIR_COMMISSION_RATE: float = Field(default=0.05, validation_alias="BETFAIR_COMMISSION_RATE")
    PINNACLE_CLIENT_ID: str = Field(default="", validation_alias="PINNACLE_CLIENT_ID")
    PINNACLE_PASSWORD: str = Field(default="", validation_alias="PINNACLE_PASSWORD")
    PINNACLE_COMMISSION_RATE: float = Field(default=0.0, validation_alias="PINNACLE_COMMISSION_RATE")
    TELEGRAM_BOT_TOKEN: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", validation_alias="TELEGRAM_CHAT_ID")
    ODDS_API_KEY: str = Field(default="", validation_alias="ODDS_API_KEY")
    FOOTBALL_DATA_ORG_TOKEN: str = Field(default="", validation_alias="FOOTBALL_DATA_ORG_TOKEN")
    FOOTBALL_API_KEY: str = Field(default="", validation_alias="FOOTBALL_API_KEY")

    # Alert Configuration
    SMTP_HOST: str = Field(default="", validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: str = Field(default="", validation_alias="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", validation_alias="SMTP_PASSWORD")
    ALERT_EMAIL_TO: str = Field(default="", validation_alias="ALERT_EMAIL_TO")
    ALERT_TELEGRAM_ENABLED: bool = Field(default=True, validation_alias="ALERT_TELEGRAM_ENABLED")
    ALERT_EMAIL_ENABLED: bool = Field(default=True, validation_alias="ALERT_EMAIL_ENABLED")

    # Ensemble Configuration
    ENSEMBLE_METHOD: str = Field(default="single", validation_alias="ENSEMBLE_METHOD")

    # Zero-cost local mode (Parquet lake, no paid APIs required)
    ZERO_COST_MODE: bool = Field(default=True, validation_alias="ZERO_COST_MODE")
    DATA_DIR: str = Field(default="data", validation_alias="DATA_DIR")
    PAPER_TRADING_ONLY: bool = Field(default=True, validation_alias="PAPER_TRADING_ONLY")
    PAPER_BANKROLL: float = Field(default=1000.0, validation_alias="PAPER_BANKROLL")
    
    # Database (with validation alias for environment compatibility)
    DB_USER: str = Field(default="vb_admin", validation_alias="POSTGRES_USER")
    DB_PASS: str = Field(default="", validation_alias="POSTGRES_PASSWORD")
    DB_HOST: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    DB_PORT: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    DB_NAME: str = Field(default="valuebetting", validation_alias="POSTGRES_DB")

    # Redis Cache
    REDIS_HOST: str = Field(default="redis", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", validation_alias="REDIS_PASSWORD")

    # API Server Config
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    API_PORT: int = Field(default=8000, validation_alias="API_PORT")
    JWT_SECRET_KEY: str = Field(default="", validation_alias="JWT_SECRET_KEY")
    ENCRYPTION_KEY: str = Field(default="", validation_alias="ENCRYPTION_KEY")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8000", validation_alias="ALLOWED_ORIGINS")
    RATE_LIMIT_ENABLED: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    
    # Risk Limits
    MAX_DAILY_LOSS_PCT: float = Field(default=5.0, validation_alias="MAX_DAILY_LOSS_PCT")
    KELLY_MULTIPLIER: float = Field(default=0.25, validation_alias="KELLY_MULTIPLIER")
    MAX_DRAWDOWN_PCT: float = Field(default=20.0, validation_alias="MAX_DRAWDOWN_PCT")
    MAX_LOSS_STREAK: int = Field(default=5, validation_alias="MAX_LOSS_STREAK")
    MAX_VOLATILITY_THRESHOLD: float = Field(default=2.0, validation_alias="MAX_VOLATILITY_THRESHOLD")
    MAX_BRIER_INCREASE: float = Field(default=0.05, validation_alias="MAX_BRIER_INCREASE")  # Zeta breaker

    # Stake safety limits (Tier D+ — prevent typo-driven catastrophic bets)
    MAX_STAKE_EUR: float = Field(default=50.0, validation_alias="MAX_STAKE_EUR")
    CONFIRMATION_THRESHOLD_EUR: float = Field(default=1.0, validation_alias="CONFIRMATION_THRESHOLD_EUR")

    # Balance Validation (Tier C+)
    BALANCE_MAX_DRIFT_PCT: float = Field(default=5.0, validation_alias="BALANCE_MAX_DRIFT_PCT")
    BALANCE_MAX_AGE_SECONDS: float = Field(default=60.0, validation_alias="BALANCE_MAX_AGE_SECONDS")
    BALANCE_MIN_RESERVE_PCT: float = Field(default=5.0, validation_alias="BALANCE_MIN_RESERVE_PCT")

    # Logging (Tier C+)
    LOG_FORMAT: str = Field(default="json", validation_alias="LOG_FORMAT")
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    LOG_FILE: str = Field(default="", validation_alias="LOG_FILE")

    # Prefect Orchestration
    PREFECT_API_URL: str = Field(default="", validation_alias="PREFECT_API_URL")
    PREFECT_API_DATABASE_CONNECTION_URL: str = Field(default="", validation_alias="PREFECT_API_DATABASE_CONNECTION_URL")

    # MLflow
    MLFLOW_TRACKING_URI: str = Field(default="", validation_alias="MLFLOW_TRACKING_URI")
    MLFLOW_EXPERIMENT_NAME: str = Field(default="nba_value_betting", validation_alias="MLFLOW_EXPERIMENT_NAME")

settings = Settings()


def _check_default_secrets():
    """Refuse to start if default/unsafe secrets are detected in ANY environment."""
    import logging
    logger = logging.getLogger(__name__)
    unsafe_defaults = []
    if settings.DB_PASS.lower() in ("postgres", "password", "1234", ""):
        unsafe_defaults.append("DB_PASS")
    if settings.JWT_SECRET_KEY in ("", "secret", "changeme"):
        unsafe_defaults.append("JWT_SECRET_KEY")
    if settings.ENCRYPTION_KEY in ("", "secret"):
        unsafe_defaults.append("ENCRYPTION_KEY")
    if unsafe_defaults:
        logger.error(
            "SECURITY: Default secrets detected for %s in %s environment. Refuse to start.",
            unsafe_defaults, settings.ENVIRONMENT
        )
        raise RuntimeError(f"Default secrets detected: {unsafe_defaults}. Set secure values before starting.")


check_default_secrets = _check_default_secrets
