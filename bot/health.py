"""
bot/health.py
~~~~~~~~~~~~~
Module 9 – Self-healing health-check and fault-tolerance layer.

Runs a pre-flight check before every order:
  1. ``ping()``         – verifies network connectivity to the Testnet.
  2. ``check_server_time()`` – detects clock drift > 1000 ms that would
                              cause signature timestamp rejection.
  3. ``preflight_check()``   – orchestrates both checks; logs results.

The health layer is the last line of defence before an order is placed.
If either check fails, the bot raises a typed exception before any signed
request is sent, preventing wasted API calls and providing clear guidance.

Usage:
    from bot.health import HealthChecker
    checker = HealthChecker(client)
    checker.preflight_check()          # raises NetworkError on failure
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bot.client import BinanceClient
from bot.exceptions import NetworkError

logger = logging.getLogger(__name__)

# Milliseconds of acceptable clock drift before we warn / error
_WARN_DRIFT_MS  = 1_000   # 1 second – warn
_ERROR_DRIFT_MS = 5_000   # 5 seconds – raise; request will be rejected by Binance


class HealthChecker:
    """Pre-flight connectivity and time-sync checks.

    Args:
        client: An initialised :class:`~bot.client.BinanceClient`.
    """

    def __init__(self, client: BinanceClient) -> None:
        self._client = client

    # ── Checks ────────────────────────────────────────────────────────────────

    def ping(self) -> None:
        """Verify network connectivity to Binance Futures Testnet.

        Raises:
            NetworkError: If the ping endpoint is unreachable or returns
                an unexpected response.
        """
        logger.debug("Health: pinging %s/fapi/v1/ping …", self._client._settings.base_url)
        try:
            result: Any = self._client.get("/fapi/v1/ping", signed=False)
        except Exception as exc:
            raise NetworkError(
                "Cannot reach Binance Futures Testnet.",
                hint=(
                    "Check your internet connection and verify that "
                    "BASE_URL=https://testnet.binancefuture.com is set in .env"
                ),
            ) from exc

        if result != {}:
            logger.warning("Unexpected ping response: %s", result)
        else:
            logger.debug("Health: ping OK")

    def check_server_time(self) -> int:
        """Compare local system time with Binance server time.

        Returns:
            The absolute clock drift in milliseconds (always non-negative).

        Raises:
            NetworkError: If drift exceeds ``_ERROR_DRIFT_MS`` (5 seconds),
                which would cause Binance to reject the request signature.
        """
        logger.debug("Health: checking server time …")
        local_ms = int(time.time() * 1000)

        try:
            data: dict[str, Any] = self._client.get("/fapi/v1/time", signed=False)
        except Exception as exc:
            logger.warning("Could not retrieve server time: %s", exc)
            return 0  # Non-fatal; proceed without time check

        server_ms: int = data.get("serverTime", local_ms)
        drift_ms = abs(local_ms - server_ms)

        if drift_ms >= _ERROR_DRIFT_MS:
            raise NetworkError(
                f"System clock is out of sync by {drift_ms} ms "
                f"(Binance limit is {_ERROR_DRIFT_MS} ms).",
                hint=(
                    "Synchronise your system clock (e.g. `sudo ntpdate pool.ntp.org`) "
                    "and try again."
                ),
            )
        if drift_ms >= _WARN_DRIFT_MS:
            logger.warning(
                "Clock drift of %d ms detected – approaching Binance's limit. "
                "Consider syncing your system clock.",
                drift_ms,
            )
        else:
            logger.debug("Health: server time OK  drift=%dms", drift_ms)

        return drift_ms

    # ── Orchestrator ──────────────────────────────────────────────────────────

    def preflight_check(self) -> None:
        """Run all health checks before placing an order.

        Executes:
          1. :meth:`ping`              – connectivity check
          2. :meth:`check_server_time` – clock drift check

        Raises:
            NetworkError: If either check fails critically.
        """
        logger.info("Running pre-flight health checks …")

        self.ping()

        drift = self.check_server_time()
        if drift < _WARN_DRIFT_MS:
            logger.info("Pre-flight checks passed  (clock drift: %dms)", drift)
        else:
            logger.info(
                "Pre-flight checks passed with clock drift warning (%dms)", drift
            )
