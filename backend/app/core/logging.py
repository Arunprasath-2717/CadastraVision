"""
app/core/logging.py
───────────────────
Structured logging configuration for CadastraVision backend.

Features
────────
* JSON-style key=value log lines in production for easy ingestion by
  log aggregators (Loki, CloudWatch, Datadog, etc.)
* Human-readable coloured output in development.
* Log level driven by settings.LOG_LEVEL.
* Call ``setup_logging()`` once at application startup.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.core.config import get_settings

_CONFIGURED = False


class _DevFormatter(logging.Formatter):
    """
    Development formatter — coloured, easy-to-read output.

    Format: [LEVEL]  YYYY-MM-DD HH:MM:SS  logger_name — message
    """

    _COLOURS: dict[int, str] = {
        logging.DEBUG:    "\033[36m",   # cyan
        logging.INFO:     "\033[32m",   # green
        logging.WARNING:  "\033[33m",   # yellow
        logging.ERROR:    "\033[31m",   # red
        logging.CRITICAL: "\033[35m",   # magenta
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        colour = self._COLOURS.get(record.levelno, "")
        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        msg = super().format(record)
        return f"{colour}[{record.levelname:<8}]{self._RESET} {ts}  {record.name} — {record.getMessage()}"


class _ProdFormatter(logging.Formatter):
    """
    Production formatter — structured key=value lines.

    Example:
        level=INFO ts=2026-08-24T10:00:00 logger=app.main msg="Server ready"
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        ts = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        line = (
            f'level={record.levelname} '
            f'ts={ts} '
            f'logger={record.name} '
            f'msg="{record.getMessage()}"'
        )
        if record.exc_info:
            line += f' exc="{self.formatException(record.exc_info)}"'
        return line


def setup_logging() -> None:
    """
    Configure the root logger.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.is_production:
        handler.setFormatter(_ProdFormatter())
    else:
        handler.setFormatter(_DevFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    # Remove any handlers added by imported libraries before our setup.
    root.handlers.clear()
    root.addHandler(handler)

    # Reduce verbosity of noisy third-party loggers.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper — returns a named logger.

    Usage::

        from app.core.logging import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
