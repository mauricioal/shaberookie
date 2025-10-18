"""Logging configuration utilities for shaberookie."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Dict, Optional

from .exceptions import ConfigurationError

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s "
    "[user_id=%(user_id)s request_id=%(request_id)s]"
)


def _build_logging_dict(log_level: str, log_dir: Path) -> Dict[str, object]:
    log_dir.mkdir(parents=True, exist_ok=True)
    access_log = log_dir / "access.log"
    error_log = log_dir / "error.log"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": DEFAULT_LOG_FORMAT,
            },
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": (
                    "%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(user_id)s %(request_id)s"
                ),
            },
        },
        "filters": {
            "context_filter": {
                "()": "shaberookie.common.logging_config.RequestContextFilter",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "filters": ["context_filter"],
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json",
                "filename": str(access_log),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["context_filter"],
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(error_log),
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["context_filter"],
            },
        },
        "loggers": {
            "shaberookie": {
                "handlers": ["console", "access_file", "error_file"],
                "level": log_level,
                "propagate": False,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }


class RequestContextFilter(logging.Filter):
    """Inject contextual defaults into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "user_id"):
            record.user_id = "n/a"
        if not hasattr(record, "request_id"):
            record.request_id = "n/a"
        return True


def configure_logging(
    *, log_level: Optional[str] = None, log_dir: Optional[Path] = None
) -> None:
    """
    Configure structured logging for the application.

    Parameters
    ----------
    log_level:
        Optional override for the log level (defaults to INFO).
    log_dir:
        Optional directory for log files (defaults to ./logs).
    """
    try:
        effective_log_dir = log_dir or Path("logs")
        logging_config = _build_logging_dict(log_level or "INFO", effective_log_dir)
        logging.config.dictConfig(logging_config)
    except Exception as exc:  # pragma: no cover - defensive log setup
        raise ConfigurationError(f"Failed to configure logging: {exc}") from exc