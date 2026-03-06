"""
bot/orders.py
~~~~~~~~~~~~~
Module 7 – Order placement business logic.

Provides high-level methods for placing MARKET and LIMIT futures orders
on Binance Futures Testnet. Delegates all HTTP communication to
``BinanceClient`` and returns clean, parsed response dictionaries.

Usage:
    from bot.config import load_settings
    from bot.client import BinanceClient
    from bot.orders import OrderManager

    settings = load_settings()
    client   = BinanceClient(settings)
    manager  = OrderManager(client)

    response = manager.place_market_order("BTCUSDT", "BUY", 0.001)
    response = manager.place_limit_order("BTCUSDT", "SELL", 0.001, 50000.0)
"""

from __future__ import annotations

import logging
from typing import Any

from bot.client import BinanceClient

logger = logging.getLogger(__name__)

_ORDER_ENDPOINT = "/fapi/v1/order"


class OrderManager:
    """Manages order placement on Binance Futures Testnet.

    Args:
        client: An initialised :class:`~bot.client.BinanceClient`.
    """

    def __init__(self, client: BinanceClient) -> None:
        self._client = client

    # ── MARKET ────────────────────────────────────────────────────────────────

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> dict[str, Any]:
        """Place a MARKET order on Binance Futures Testnet.

        A MARKET order executes immediately at the best available price.
        No ``price`` parameter is sent.

        Args:
            symbol:   Trading pair, e.g. ``"BTCUSDT"``.
            side:     ``"BUY"`` or ``"SELL"``.
            quantity: Order size in base asset units.

        Returns:
            Parsed Binance order response dictionary containing at minimum:
            ``orderId``, ``status``, ``executedQty``, ``avgPrice``.

        Raises:
            BinanceAPIError: On invalid parameters or insufficient margin.
            NetworkError:    If the API is unreachable after retries.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }
        logger.info(
            "Placing MARKET order: symbol=%s side=%s qty=%s",
            symbol, side, quantity,
        )
        response = self._client.post(_ORDER_ENDPOINT, params=params)
        logger.info(
            "MARKET order placed: orderId=%s status=%s executedQty=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
        )
        return response

    # ── LIMIT ─────────────────────────────────────────────────────────────────

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        """Place a LIMIT order on Binance Futures Testnet.

        A LIMIT order rests on the book until the market reaches *price*.

        Args:
            symbol:        Trading pair, e.g. ``"BTCUSDT"``.
            side:          ``"BUY"`` or ``"SELL"``.
            quantity:      Order size in base asset units.
            price:         Limit price in quote asset (USDT).
            time_in_force: Order duration policy (default ``"GTC"`` – Good Till
                           Cancelled).

        Returns:
            Parsed Binance order response dictionary.

        Raises:
            BinanceAPIError: On invalid parameters or price filter violations.
            NetworkError:    If the API is unreachable after retries.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
        }
        logger.info(
            "Placing LIMIT order: symbol=%s side=%s qty=%s price=%s timeInForce=%s",
            symbol, side, quantity, price, time_in_force,
        )
        response = self._client.post(_ORDER_ENDPOINT, params=params)
        logger.info(
            "LIMIT order placed: orderId=%s status=%s",
            response.get("orderId"),
            response.get("status"),
        )
        return response
