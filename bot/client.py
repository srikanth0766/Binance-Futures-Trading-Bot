"""
bot/client.py
~~~~~~~~~~~~~
Module 6 – Binance Futures REST API HTTP client.

Handles:
  • HMAC-SHA256 request signing
  • Persistent ``requests.Session`` with configurable timeouts
  • Exponential-backoff retry (up to 3 attempts) for transient failures
  • DEBUG-level logging of every outgoing request and incoming response
  • Translation of Binance error bodies into typed ``BinanceAPIError`` exceptions

Usage:
    from bot.config import load_settings
    from bot.client import BinanceClient
    client = BinanceClient(settings)
    response = client.post("/fapi/v1/order", params={...})
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import random
import time
import urllib.parse
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.config import Settings
from bot.exceptions import BinanceAPIError, NetworkError, SignatureError

logger = logging.getLogger(__name__)


# ─── Retry / timeout constants ────────────────────────────────────────────────

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0          # seconds: 1s → 2s → 4s
_BACKOFF_JITTER = 0.5        # ± seconds of random jitter per attempt
_CONNECT_TIMEOUT = 5.0       # seconds to establish connection
_READ_TIMEOUT = 10.0         # seconds to receive the first byte
_TIMEOUT = (_CONNECT_TIMEOUT, _READ_TIMEOUT)

# Retry on these HTTP status codes (server-side transient errors)
_RETRY_STATUS_CODES = {500, 502, 503, 504}


# ─── Client ───────────────────────────────────────────────────────────────────


class BinanceClient:
    """Low-level Binance Futures REST client with signing and retry.

    Args:
        settings: Bot configuration (API key, secret, base URL, recv_window).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session = self._build_session()
        logger.debug(
            "BinanceClient initialised: base_url=%s recv_window=%dms",
            settings.base_url,
            settings.recv_window,
        )

    # ── Session factory ───────────────────────────────────────────────────────

    @staticmethod
    def _build_session() -> requests.Session:
        """Create a ``requests.Session`` with connection-pool retries for
        network-level issues (DNS, reset, etc.), separate from application-
        level retries handled in ``_request_with_retry``."""
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=0,               # application-level retry handles it
                allowed_methods=False,
                raise_on_status=False,
            )
        )
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        return session

    # ── Signing ───────────────────────────────────────────────────────────────

    def _sign(self, query_string: str) -> str:
        """Generate an HMAC-SHA256 signature for *query_string*.

        Args:
            query_string: URL-encoded parameter string to sign.

        Returns:
            Hex-encoded signature string.

        Raises:
            SignatureError: If the secret key is missing or signing fails.
        """
        secret = self._settings.secret_key
        if not secret:
            raise SignatureError(
                "Cannot sign request: secret key is empty.",
                hint="Ensure BINANCE_SECRET_KEY is set in .env",
            )
        try:
            return hmac.new(
                secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        except Exception as exc:
            raise SignatureError(f"HMAC signing failed: {exc}") from exc

    def _build_params(self, params: dict[str, Any], signed: bool) -> dict[str, Any]:
        """Add timestamp (and signature if required) to *params*.

        Args:
            params: Base request parameters.
            signed: Whether to append ``timestamp`` and ``signature``.

        Returns:
            A new dict with the extra fields appended.
        """
        full_params = dict(params)   # copy – do not mutate caller's dict
        if signed:
            full_params["timestamp"] = int(time.time() * 1000)
            full_params["recvWindow"] = self._settings.recv_window
            query_string = urllib.parse.urlencode(full_params)
            full_params["signature"] = self._sign(query_string)
        return full_params

    # ── Core request ──────────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """Execute a single HTTP request.

        Args:
            method: HTTP verb (``"GET"`` or ``"POST"``).
            path:   API path, e.g. ``"/fapi/v1/order"``.
            params: Query / form parameters.
            signed: If ``True``, attach timestamp and HMAC signature.

        Returns:
            Parsed JSON response as a dict.

        Raises:
            BinanceAPIError: If Binance returns an error payload.
            NetworkError:    On timeouts or connection failures.
        """
        url = self._settings.base_url + path
        full_params = self._build_params(params or {}, signed=signed)

        # Log the outgoing request (mask secret key in logs)
        safe_params = {k: v for k, v in full_params.items() if k != "signature"}
        logger.debug("→ %s %s  params=%s", method, url, safe_params)

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=full_params, timeout=_TIMEOUT)
            else:
                response = self._session.post(url, data=full_params, timeout=_TIMEOUT)
        except requests.exceptions.Timeout as exc:
            raise NetworkError("Request timed out.", hint="Check your internet connection or retry.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Cannot connect to {url}.", hint="Verify your internet connection and the BASE_URL in .env.") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"Unexpected network error: {exc}") from exc

        logger.debug("← HTTP %d  body=%s", response.status_code, response.text[:500])

        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: requests.Response) -> dict[str, Any]:
        """Parse the response and raise on Binance error bodies.

        Args:
            response: The raw ``requests.Response`` object.

        Returns:
            Parsed JSON as a dict.

        Raises:
            BinanceAPIError: For Binance-level errors (even on HTTP 200 if
                the body contains ``{"code": <negative>, "msg": ...}``).
        """
        try:
            data: dict[str, Any] = response.json()
        except ValueError:
            # Non-JSON response – treat as network/server error
            raise NetworkError(
                f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}",
                hint="The testnet may be temporarily unavailable.",
            )

        # Binance signals application-level errors with a negative "code" key
        if isinstance(data, dict) and data.get("code", 0) < 0:
            raise BinanceAPIError(code=data["code"], msg=data.get("msg", "Unknown error"))

        # Propagate HTTP-level errors that Binance didn't wrap in JSON
        if not response.ok:
            raise BinanceAPIError(
                code=response.status_code,
                msg=f"HTTP {response.status_code}: {response.reason}",
            )

        return data

    # ── Retry wrapper ─────────────────────────────────────────────────────────

    def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """Retry ``_request`` up to ``_MAX_RETRIES`` times on transient errors.

        Retry policy:
          • ``NetworkError`` (timeouts, connection failures) → always retry
          • ``BinanceAPIError`` with HTTP 5xx status → retry
          • Backoff: 1s, 2s, 4s  ± up to 0.5s random jitter

        Args:
            method: HTTP verb.
            path:   API path.
            params: Request parameters.
            signed: Whether to sign the request.

        Returns:
            Parsed JSON response dict.

        Raises:
            NetworkError | BinanceAPIError: After all retry attempts are
                exhausted.
        """
        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return self._request(method, path, params, signed)

            except NetworkError as exc:
                last_exc = exc
                logger.warning(
                    "Network error on attempt %d/%d: %s",
                    attempt, _MAX_RETRIES, exc.message,
                )

            except BinanceAPIError as exc:
                # Only retry on server-side 5xx codes; any app-level negative
                # code should bubble up immediately.
                if exc.code in _RETRY_STATUS_CODES:
                    last_exc = exc
                    logger.warning(
                        "Server error %d on attempt %d/%d – retrying …",
                        exc.code, attempt, _MAX_RETRIES,
                    )
                else:
                    raise

            if attempt < _MAX_RETRIES:
                wait = _BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(
                    -_BACKOFF_JITTER, _BACKOFF_JITTER
                )
                wait = max(0, wait)
                logger.info("Waiting %.2fs before retry %d …", wait, attempt + 1)
                time.sleep(wait)

        assert last_exc is not None
        logger.error("All %d retry attempts failed: %s", _MAX_RETRIES, last_exc)
        raise last_exc

    # ── Public helpers ────────────────────────────────────────────────────────

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        """Perform a GET request with automatic retry.

        Args:
            path:   API path.
            params: Query parameters.
            signed: If ``True``, attach timestamp + HMAC signature.

        Returns:
            Parsed JSON response dict.
        """
        return self._request_with_retry("GET", path, params, signed)

    def post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """Perform a POST request with automatic retry.

        Args:
            path:   API path.
            params: Form parameters (sent as ``application/x-www-form-urlencoded``).
            signed: If ``True``, attach timestamp + HMAC signature (default).

        Returns:
            Parsed JSON response dict.
        """
        return self._request_with_retry("POST", path, params, signed)
