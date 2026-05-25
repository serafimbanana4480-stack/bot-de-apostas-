"""
Async Database Session Factory.

Creates a global ``AsyncEngine`` and ``async_sessionmaker`` driven by
the values in :pymod:`src.core.config`.  Use ``get_session`` as a
FastAPI dependency or as an async context manager::

    async for session in get_session():
        await session.execute(...)
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

# ---------------------------------------------------------------------------
# Engine singleton
# ---------------------------------------------------------------------------
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    """Create and return the async engine (idempotent)."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.DB_ECHO_SQL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,
        )
    return _engine


def _build_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create and return the session factory (idempotent)."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_build_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


def get_engine() -> AsyncEngine:
    """Return the async engine (creates it on first call)."""
    return _build_engine()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory (creates it on first call)."""
    return _build_session_factory()


# ---------------------------------------------------------------------------
# FastAPI dependency / context manager
# ---------------------------------------------------------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` and handle commit / rollback.

    Intended as a FastAPI ``Depends`` or standalone async context::

        async for session in get_session():
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------
async def init_db() -> None:
    """Import models and create all tables (development convenience).

    In production, use Alembic migrations instead.
    """
    from src.database.models import Base  # noqa: F811

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine connection pool."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
