"""
Correlation ID propagation for end-to-end bet tracing.

Every bet receives a UUID at ingestion and that ID permeates all logs,
metrics, and audit records across ingestion → decision → execution → settlement.

Usage:
    from src.monitoring.correlation_context import correlation_ctx, get_correlation_id

    with correlation_ctx("abc-123"):
        logger.info("Decision made", extra={"event_id": "evt-1"})
        # JSON log will include "correlation_id": "abc-123"
"""
from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Generator

# Thread-safe / async-safe correlation ID storage
_CORRELATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str | None:
    """Return the current correlation ID for this execution context."""
    return _CORRELATION_ID.get()


def set_correlation_id(cid: str | None) -> None:
    """Explicitly set the correlation ID (useful in async callbacks)."""
    _CORRELATION_ID.set(cid)


def generate_correlation_id(prefix: str = "vbq") -> str:
    """Generate a new correlation ID."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@contextmanager
def correlation_ctx(cid: str | None = None) -> Generator[None, None, None]:
    """
    Context manager that sets a correlation ID for the current execution scope.
    Automatically generates one if not provided.
    """
    if cid is None:
        cid = generate_correlation_id()
    token = _CORRELATION_ID.set(cid)
    try:
        yield
    finally:
        _CORRELATION_ID.reset(token)
