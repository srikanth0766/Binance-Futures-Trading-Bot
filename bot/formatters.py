"""
bot/formatters.py
~~~~~~~~~~~~~~~~~
Module 8 – Human-readable terminal output formatter.

Renders order request summaries and API responses to stdout using ANSI
colour codes.  Degrades gracefully when stdout is not a TTY (colours are
stripped automatically via ``_supports_colour()``).

Usage:
    from bot.formatters import format_order_summary, format_order_response, format_error
    format_order_summary(params)
    format_order_response(response)
    format_error(exc)
"""

from __future__ import annotations

import sys
from typing import Any


# ─── ANSI helpers ─────────────────────────────────────────────────────────────

class _Colour:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"


def _supports_colour() -> bool:
    """Return ``True`` if the terminal supports ANSI escape codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, *codes: str) -> str:
    """Wrap *text* in ANSI colour codes if the terminal supports them."""
    if not _supports_colour():
        return text
    return "".join(codes) + text + _Colour.RESET


def _box(title: str, rows: list[tuple[str, str]], colour: str = _Colour.CYAN) -> None:
    """Print a simple bordered table to stdout.

    Args:
        title:  Box header text.
        rows:   List of (label, value) pairs.
        colour: ANSI colour code to apply to the border (default cyan).
    """
    key_width = max((len(k) for k, _ in rows), default=8) + 2
    val_width = max((len(str(v)) for _, v in rows), default=20) + 2
    width = key_width + val_width + 3  # 2 borders + 1 separator

    border = _c("═" * width, colour)
    sep    = _c("─" * width, colour)

    print()
    print(_c(f" {title} ", colour, _Colour.BOLD).center(width + 20))
    print(_c("╔" + "═" * width + "╗", colour))
    for key, val in rows:
        k_str = _c(f" {key:<{key_width - 1}}", _Colour.WHITE, _Colour.BOLD)
        v_str = f" {val!s:<{val_width - 1}}"
        print(_c("║", colour) + k_str + _c("│", colour) + v_str + _c("║", colour))
    print(_c("╚" + "═" * width + "╝", colour))
    print()


# ─── Public formatters ────────────────────────────────────────────────────────


def format_order_summary(params: Any) -> None:
    """Print a formatted table of the order that *will* be submitted.

    Args:
        params: An :class:`~bot.validators.OrderParams` instance or any object
                with ``symbol``, ``side``, ``order_type``, ``quantity``,
                and ``price`` attributes.
    """
    rows = [
        ("Symbol",     params.symbol),
        ("Side",       params.side),
        ("Order Type", params.order_type),
        ("Quantity",   params.quantity),
        ("Price",      params.price if params.price is not None else "MARKET"),
    ]
    _box("ORDER REQUEST", rows, colour=_Colour.CYAN)


def format_order_response(response: dict[str, Any]) -> None:
    """Print the key fields from a Binance order response.

    Displays: orderId, status, executedQty, avgPrice, side, type, symbol.

    Args:
        response: Parsed JSON dict returned by the Binance Futures API.
    """
    status = response.get("status", "UNKNOWN")
    colour = _Colour.GREEN if status in {"FILLED", "NEW", "PARTIALLY_FILLED"} else _Colour.YELLOW

    avg_price = response.get("avgPrice") or response.get("price", "N/A")
    rows = [
        ("Order ID",     response.get("orderId", "N/A")),
        ("Status",       status),
        ("Symbol",       response.get("symbol", "N/A")),
        ("Side",         response.get("side", "N/A")),
        ("Type",         response.get("type", "N/A")),
        ("Executed Qty", response.get("executedQty", "0")),
        ("Avg Price",    avg_price),
    ]
    _box("ORDER RESPONSE", rows, colour=colour)
    print(_c("  ✓ Order submitted successfully!", _Colour.GREEN, _Colour.BOLD))
    print()


def format_error(error: Exception) -> None:
    """Print a red error banner to stdout.

    Args:
        error: The exception to display. If it has a ``hint`` attribute
               (e.g. :class:`~bot.exceptions.TradingBotError`), the hint is
               printed on a second line.
    """
    message = getattr(error, "message", str(error))
    hint    = getattr(error, "hint", "")

    print()
    print(_c("  ✗ ERROR", _Colour.RED, _Colour.BOLD))
    print(_c(f"  {message}", _Colour.RED))
    if hint:
        print(_c(f"  → {hint}", _Colour.YELLOW))
    print()
