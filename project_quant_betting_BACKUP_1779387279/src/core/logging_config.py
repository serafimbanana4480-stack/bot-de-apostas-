"""
Structured Logging Configuration.

Provides JSON-formatted logs with correlation IDs for request tracing,
rotating file handlers for production, and a clean console fallback for
development.

Usage::

    from src.core.logging_config import get_logger, set_correlation_id

    logger = get_logger(__name__)
    set_correlation_id("req-abc-123")
    logger.info("Processing bet", extra={"market_id": "1.234"})
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Correlation ID management (async-safe via contextvars)
# ---------------------------------------------------------------------------
_correlation_id: ContextVar[str] = ContextVar(
    "correlation_id", default=""
)


def set_correlation_id(cid: str | None = None) -> str:
    """Set (or generate) a correlation ID for the current async context.

    Args:
        cid: Optional explicit ID. A UUID4 is generated when ``None``.

    Returns:
        The active correlation ID.
    """
    value = cid or uuid.uuid4().hex[:12]
    _correlation_id.set(value)
    return value


def get_correlation_id() -> str:
    """Return the current correlation ID (empty string if unset)."""
    return _correlation_id.get()


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects.

    Each record includes a UTC ISO-8601 timestamp, correlation ID,
    level, logger name, message, and any ``extra`` fields passed by the
    caller.
    """

    # Fields from LogRecord that are part of the standard schema and should
    # NOT be duplicated into the ``extra`` bucket.
    _BUILTIN_ATTRS: frozenset[str] = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
    ) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        # Location context (useful in DEBUG / ERROR)
        if record.levelno >= logging.WARNING:
            payload["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Exception info
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception"] = self.formatException(record.exc_info)

        # Merge caller-supplied ``extra`` fields.
        for key, value in record.__dict__.items():
            if key not in self._BUILTIN_ATTRS:
                payload[key] = value

        return json.dumps(payload, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Human-readable coloured formatter for local development."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        color = self.COLORS.get(record.levelname, "")
        cid = get_correlation_id()
        cid_str = f"[{cid}] " if cid else ""
        ts = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%H:%M:%S.%f")[:-3]
        return (
            f"{color}{ts} {record.levelname:<8}{self.RESET} "
            f"{cid_str}{record.name} — {record.getMessage()}"
        )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def setup_logging(
    *,
    level: str = "INFO",
    log_format: str = "json",
    log_file: str | None = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """Configure the root logger.

    Args:
        level: Minimum log level (``DEBUG``, ``INFO``, …).
        log_format: ``"json"`` for production, ``"text"`` for dev.
        log_file: Path to the rotating log file. ``None`` disables file
            logging.
        max_bytes: Maximum bytes per log file before rotation.
        backup_count: Number of rotated files to keep.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Clear existing handlers (safe for re-entry)
    root.handlers.clear()

    # --- Console handler ---
    console = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        console.setFormatter(JSONFormatter())
    else:
        console.setFormatter(ConsoleFormatter())
    root.addHandler(console)

    # --- Rotating file handler ---
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        root.addHandler(file_handler)

    # Quiet noisy third-party loggers
    for name in ("asyncio", "aiohttp", "urllib3", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    This is a thin wrapper that ensures ``setup_logging`` has been called
    at least once before any logger is used.

    Args:
        name: Typically ``__name__`` of the calling module.
    """
    return logging.getLogger(name)
