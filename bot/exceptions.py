"""
bot/exceptions.py
~~~~~~~~~~~~~~~~~
Module 3 – Custom exception hierarchy for the trading bot.

All exceptions derive from ``TradingBotError`` so callers can catch the
entire family with a single ``except TradingBotError`` clause, while still
being able to distinguish individual failure modes when needed.

Hierarchy:
    TradingBotError
    ├── ConfigurationError
    ├── ValidationError
    ├── NetworkError
    ├── BinanceAPIError
    └── SignatureError
"""

from __future__ import annotations


class TradingBotError(Exception):
    """Base exception for all trading-bot errors.

    Args:
        message: Human-readable description of the error.
        hint:    Optional corrective action to display to the user.
    """

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n  → Hint: {self.hint}"
        return self.message


# ─── Configuration ────────────────────────────────────────────────────────────


class ConfigurationError(TradingBotError):
    """Raised when required environment variables are missing or invalid.

    Example:
        raise ConfigurationError(
            "BINANCE_API_KEY is not set",
            hint="Copy .env.example to .env and fill in your testnet API key",
        )
    """


# ─── Validation ───────────────────────────────────────────────────────────────


class ValidationError(TradingBotError):
    """Raised when user-supplied CLI input fails validation.

    Attributes:
        field: The name of the parameter that failed validation.

    Example:
        raise ValidationError("Quantity must be positive", field="quantity")
    """

    def __init__(self, message: str, field: str = "", hint: str = "") -> None:
        super().__init__(message, hint=hint)
        self.field = field

    def __str__(self) -> str:
        prefix = f"[{self.field}] " if self.field else ""
        base = f"{prefix}{self.message}"
        if self.hint:
            return f"{base}\n  → Hint: {self.hint}"
        return base


# ─── Network ──────────────────────────────────────────────────────────────────


class NetworkError(TradingBotError):
    """Raised when the bot cannot reach the Binance Futures Testnet.

    This covers DNS failures, connection refused, and timeout errors.

    Example:
        raise NetworkError(
            "Connection timed out after 3 retries",
            hint="Check your internet connection or try again later",
        )
    """


# ─── Binance API ──────────────────────────────────────────────────────────────


class BinanceAPIError(TradingBotError):
    """Raised when Binance returns a non-2xx or an error-code response.

    Attributes:
        code: Binance error code (negative integer, e.g. -1121).
        msg:  Binance error message string.

    Example:
        raise BinanceAPIError(
            code=-1121,
            msg="Invalid symbol",
            hint="Ensure the symbol exists on Futures Testnet (e.g. BTCUSDT)",
        )
    """

    # Map of known Binance error codes → corrective hints
    _HINTS: dict[int, str] = {
        -1100: "One or more parameters contain illegal characters",
        -1102: "A mandatory request parameter was not sent",
        -1111: "Precision is over the maximum defined for this asset",
        -1121: "Check symbol format – use uppercase, e.g. BTCUSDT",
        -1013: "Check LOT_SIZE filter: adjust quantity to allowed step size",
        -2019: "Insufficient margin – reduce quantity or deposit more funds",
        -2011: "The order you tried to cancel does not exist",
        -2021: "The order is already filled or cancelled",
        -1003: "Too many requests – slow down and retry after a pause",
    }

    def __init__(self, code: int, msg: str, hint: str = "") -> None:
        # Auto-populate hint from the known-codes map if not provided
        resolved_hint = hint or self._HINTS.get(code, "Check Binance API docs for error code details")
        super().__init__(f"Binance API error {code}: {msg}", hint=resolved_hint)
        self.code = code
        self.msg = msg


# ─── Signature ────────────────────────────────────────────────────────────────


class SignatureError(TradingBotError):
    """Raised when HMAC-SHA256 request signing fails.

    This usually indicates a missing or malformed ``BINANCE_SECRET_KEY``.

    Example:
        raise SignatureError(
            "Failed to compute request signature",
            hint="Ensure BINANCE_SECRET_KEY is set and non-empty in .env",
        )
    """
