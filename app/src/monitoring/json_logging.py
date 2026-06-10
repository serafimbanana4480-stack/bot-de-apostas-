"""
Structured JSON logging configuration for VBQ system.

Replaces default Python logging with JSON-formatted output suitable for
ingestion by Loki, ELK, or any structured log aggregator.

Usage:
    from src.monitoring.json_logging import setup_json_logging
    setup_json_logging()

All subsequent log calls will output JSON lines like:
    {"timestamp":"2024-01-15T20:30:00","level":"INFO","name":"train","message":"Training fold 1","sport":"football"}
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON lines for structured log aggregation.

    Includes timestamp, level, logger name, message, and any extra fields
    passed via logger.info("msg", extra={...}).
    """

    def __init__(self, service_name: str = "vbq", include_extras: bool = True):
        super().__init__()
        self.service_name = service_name
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        # Include correlation ID if available in execution context
        try:
            from src.monitoring.correlation_context import get_correlation_id
            cid = get_correlation_id()
            if cid:
                log_entry["correlation_id"] = cid
        except ImportError:
            pass

        # Include exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Include any extra fields passed via logger.info("msg", extra={...})
        if self.include_extras:
            standard_attrs = {
                "name", "msg", "args", "created", "relativeCreated",
                "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "pathname", "filename", "module", "levelno", "levelname",
                "thread", "threadName", "process", "processName", "msecs",
                "taskName",
            }
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith("_"):
                    try:
                        json.dumps(value)  # Check serializable
                        log_entry[key] = value
                    except (TypeError, ValueError):
                        log_entry[key] = str(value)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class JSONLogHandler(logging.StreamHandler):
    """Stream handler that outputs JSON-formatted log lines."""

    def __init__(self, stream=None, service_name: str = "vbq"):
        super().__init__(stream or sys.stdout)
        self.setFormatter(JSONFormatter(service_name=service_name))


def setup_json_logging(
    level: int = logging.INFO,
    service_name: str = "vbq",
    log_file: Optional[str] = None,
) -> None:
    """
    Configure root logger to output structured JSON logs.

    Args:
        level: Logging level (default INFO)
        service_name: Service identifier in each log line
        log_file: Optional file path for log output (default: stdout)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add JSON handler to stdout
    json_handler = JSONLogHandler(service_name=service_name)
    root_logger.addHandler(json_handler)

    # Optional: also write to file with rotation
    if log_file:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file, encoding="utf-8", maxBytes=5_000_000, backupCount=5
        )
        file_handler.setFormatter(JSONFormatter(service_name=service_name))
        root_logger.addHandler(file_handler)

    # Silence noisy libraries
    for noisy in ("urllib3", "requests", "botocore", "google", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def setup_standard_logging(level: int = logging.INFO) -> None:
    """
    Configure standard (non-JSON) logging for development.
    Reverts to human-readable format.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )
