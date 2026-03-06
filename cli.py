#!/usr/bin/env python3
"""
cli.py
~~~~~~
Module 10 – CLI entry point for the Binance Futures Testnet trading bot.

Parses user arguments, orchestrates the bot pipeline:
  load_settings → setup_logging → validate_all → preflight_check
  → format_order_summary → place_order → format_order_response

Exit codes:
  0 – success
  1 – validation or configuration error
  2 – Binance API error
  3 – network/connectivity error

Usage examples:
  # Market BUY
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

  # Limit SELL
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 50000

  # Lowercase inputs are auto-corrected (self-healing)
  python cli.py --symbol btcusdt --side buy --type market --qty 0.001
"""

from __future__ import annotations

import argparse
import sys

from bot.config import load_settings
from bot.logging_config import setup_logging
from bot.validators import validate_all
from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.health import HealthChecker
from bot.formatters import format_order_summary, format_order_response, format_error
from bot.exceptions import (
    TradingBotError,
    ValidationError,
    ConfigurationError,
    BinanceAPIError,
    NetworkError,
)


# ─── Argument parser ──────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=(
            "Binance Futures Testnet Trading Bot\n"
            "Places MARKET and LIMIT orders on USDT-M Futures Testnet."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001\n"
            "  python cli.py --symbol BTCUSDT --side SELL --type LIMIT "
            "--qty 0.001 --price 50000\n"
        ),
    )
    parser.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT (case-insensitive)",
    )
    parser.add_argument(
        "--side",
        required=True,
        metavar="SIDE",
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type", "-t",
        dest="order_type",
        required=True,
        metavar="TYPE",
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--qty", "-q",
        required=True,
        metavar="QUANTITY",
        help="Order quantity in base asset units, e.g. 0.001",
    )
    parser.add_argument(
        "--price", "-p",
        default=None,
        metavar="PRICE",
        help="Limit price in USDT (required for LIMIT orders)",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        metavar="DIR",
        help="Directory for log files (default: ./logs/)",
    )
    return parser


# ─── Main pipeline ────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Main entry point.  Returns an exit code (0 = success, 1/2/3 = error)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # ── Step 1: Load settings ────────────────────────────────────────────────
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        # Logging is not yet set up – print directly to stderr
        print(f"\n  ✗ Configuration Error: {exc}", file=sys.stderr)
        if exc.hint:
            print(f"  → {exc.hint}", file=sys.stderr)
        return 1

    # ── Step 2: Setup logging ────────────────────────────────────────────────
    from pathlib import Path
    log_dir = Path(args.log_dir) if args.log_dir else None
    logger = setup_logging(log_dir=log_dir or Path("logs"))
    logger.info("=== Trading Bot Session Started ===")
    logger.info(
        "CLI args: symbol=%s side=%s type=%s qty=%s price=%s",
        args.symbol, args.side, args.order_type, args.qty, args.price,
    )

    # ── Step 3: Validate inputs ──────────────────────────────────────────────
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.qty,
            price=args.price,
        )
    except ValidationError as exc:
        format_error(exc)
        logger.error("Validation failed: %s", exc)
        return 1

    # ── Step 4: Show order summary ───────────────────────────────────────────
    format_order_summary(params)

    # ── Step 5: Initialise client + health check ─────────────────────────────
    try:
        client  = BinanceClient(settings)
        checker = HealthChecker(client)
        checker.preflight_check()
    except NetworkError as exc:
        format_error(exc)
        logger.error("Preflight failed (network): %s", exc)
        return 3

    # ── Step 6: Place order ──────────────────────────────────────────────────
    manager = OrderManager(client)
    try:
        if params.order_type == "MARKET":
            response = manager.place_market_order(
                symbol=params.symbol,
                side=params.side,
                quantity=params.quantity,
            )
        else:  # LIMIT
            response = manager.place_limit_order(
                symbol=params.symbol,
                side=params.side,
                quantity=params.quantity,
                price=params.price,  # type: ignore[arg-type]
            )
    except BinanceAPIError as exc:
        format_error(exc)
        logger.error("Binance API error: code=%d msg=%s", exc.code, exc.msg)
        return 2
    except NetworkError as exc:
        format_error(exc)
        logger.error("Network error during order placement: %s", exc)
        return 3

    # ── Step 7: Show response ────────────────────────────────────────────────
    format_order_response(response)
    logger.info("=== Trading Bot Session Complete ===")
    return 0


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())
