"""
bot/logging_config.py
~~~~~~~~~~~~~~~~~~~~~
Module 2 – Structured logging configuration.

Sets up a dual-output logger:
  • Rotating file handler  → logs/<log_file>  (DEBUG and above)
  • Stream (console) handler → stderr          (INFO and above)

Usage:
    from bot.logging_config import setup_logging
    logger = setup_logging()
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
DEFAULT_LOG_FILE = "trading_bot.log"
MAX_BYTES = 5 * 1024 * 1024   # 5 MB per log file
BACKUP_COUNT = 3               # keep the last 3 rotated files

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ─── Public API ───────────────────────────────────────────────────────────────


def setup_logging(
    log_dir: Path | str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> logging.Logger:
    """Configure and return the root logger for the trading bot.

    Args:
        log_dir:       Directory where log files are written (created if absent).
        log_file:      Name of the rotating log file.
        file_level:    Minimum level written to the file (default DEBUG).
        console_level: Minimum level written to the console (default INFO).

    Returns:
        The configured root ``logging.Logger`` instance.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler (rotating) ──────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # ── Root logger ─────────────────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)   # capture everything; handlers filter

    # Avoid adding duplicate handlers on repeated calls (e.g. in tests)
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    root_logger.info("Logging initialised → %s", log_path)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper – returns a named child logger.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance.
    """
    return logging.getLogger(name)
