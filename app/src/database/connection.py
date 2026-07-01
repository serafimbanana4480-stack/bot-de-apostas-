import logging

logger = logging.getLogger(__name__)

# Lazy imports — avoid hard dependency on sqlalchemy/psycopg2 at import time
# so that test modules that only need Base can import without a running DB.
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    from src.core.config import settings

    # Assemble database URL with URL-encoded credentials
    # e.g., postgresql://vb_admin:{quote_plus(settings.DB_PASS)}@localhost:5432/valuebetting
    from urllib.parse import quote_plus
    database_url = (
        f"postgresql://{quote_plus(settings.DB_USER)}:{quote_plus(settings.DB_PASS)}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

    # Replace 'localhost' if running inside docker and DB_HOST is overrideable
    # Pydantic Settings handles this via env variables dynamically.
    logger.info(f"Connecting to database at {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as _db_import_err:
    logger.warning(f"Database connection not available: {_db_import_err}")
    # Provide stubs so that imports of `Base` and `get_db` don't crash
    Base = None  # type: ignore[assignment,misc]
    engine = None  # type: ignore[assignment]
    SessionLocal = None  # type: ignore[assignment]

def get_db():
    """Dependency generator for FastAPI routes and service injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
