"""
logger.py
---------
Centralised logging configuration for the AI Tech News Aggregator.
Provides both file and console handlers with rotation support.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from config.settings import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging(name: str = "ai_news_aggregator") -> logging.Logger:
    """
    Configure and return the root application logger.

    The logger writes to both the console (stdout) and a rotating file.
    Call this function once at application startup.
    """
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger(name)
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers on repeated calls
    if root_logger.handlers:
        return root_logger

    # ── Console handler ────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ── Rotating file handler ──────────────────────────────────────────────
    try:
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(LOG_FILE),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as exc:  # pragma: no cover
        root_logger.warning("Could not create file log handler: %s", exc)

    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """Return a child logger namespaced under the application root."""
    return logging.getLogger(f"ai_news_aggregator.{module_name}")
