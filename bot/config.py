"""
bot/config.py
~~~~~~~~~~~~~
Module 5 – Environment configuration loader.

Reads API credentials and bot settings from a ``.env`` file using
``python-dotenv``.  All settings are exposed as a frozen ``Settings``
dataclass so the rest of the codebase enjoys type-safe, immutable access.

Usage:
    from bot.config import load_settings
    settings = load_settings()          # raises ConfigurationError if misconfigured
    print(settings.base_url)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from bot.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Default testnet base URL – can be overridden via .env
_DEFAULT_BASE_URL = "https://demo-fapi.binance.com"
_DEFAULT_RECV_WINDOW = 5000


# ─── Settings dataclass ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Settings:
    """Immutable bot configuration loaded from the environment.

    Attributes:
        api_key:     Binance Futures Testnet API key.
        secret_key:  Binance Futures Testnet secret key used for HMAC signing.
        base_url:    Testnet REST base URL (default: https://testnet.binancefuture.com).
        recv_window: Milliseconds the request remains valid (default: 5000).
        log_level:   Logging level string (default: DEBUG).
    """

    api_key: str
    secret_key: str
    base_url: str
    recv_window: int
    log_level: str


# ─── Loader ───────────────────────────────────────────────────────────────────


def load_settings(env_path: Path | str | None = None) -> Settings:
    """Load configuration from ``.env`` and return a ``Settings`` object.

    Search order for the ``.env`` file:
    1. ``env_path`` argument (if provided).
    2. ``<project_root>/.env`` (sibling of this file's parent directory).

    Args:
        env_path: Explicit path to a ``.env`` file, or ``None`` to auto-detect.

    Returns:
        A frozen :class:`Settings` instance.

    Raises:
        ConfigurationError: If ``BINANCE_API_KEY`` or ``BINANCE_SECRET_KEY``
            are not set in the environment after loading the ``.env`` file.
    """
    # Resolve .env location
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    else:
        env_path = Path(env_path)

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logger.debug("Loaded environment from: %s", env_path)
    else:
        logger.warning(
            ".env file not found at %s – relying on shell environment variables.",
            env_path,
        )

    # Required values
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    secret_key = os.getenv("BINANCE_SECRET_KEY", "").strip()

    missing: list[str] = []
    if not api_key:
        missing.append("BINANCE_API_KEY")
    if not secret_key:
        missing.append("BINANCE_SECRET_KEY")
    if missing:
        raise ConfigurationError(
            f"Missing required environment variable(s): {', '.join(missing)}",
            hint=(
                "Copy .env.example → .env and fill in your Binance Futures "
                "Testnet API credentials."
            ),
        )

    # Optional values with defaults
    base_url = os.getenv("BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
    recv_window_raw = os.getenv("RECV_WINDOW", str(_DEFAULT_RECV_WINDOW))
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

    try:
        recv_window = int(recv_window_raw)
    except ValueError:
        logger.warning(
            "Invalid RECV_WINDOW value '%s'; defaulting to %d ms.",
            recv_window_raw,
            _DEFAULT_RECV_WINDOW,
        )
        recv_window = _DEFAULT_RECV_WINDOW

    settings = Settings(
        api_key=api_key,
        secret_key=secret_key,
        base_url=base_url,
        recv_window=recv_window,
        log_level=log_level,
    )
    logger.info(
        "Settings loaded: base_url=%s recv_window=%dms log_level=%s",
        settings.base_url,
        settings.recv_window,
        settings.log_level,
    )
    return settings
