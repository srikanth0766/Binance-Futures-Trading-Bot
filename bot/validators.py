"""
bot/validators.py
~~~~~~~~~~~~~~~~~
Module 4 – Input validation with self-healing normalisation.

All public functions accept raw strings from the CLI, attempt automatic
correction (self-healing), and raise ``ValidationError`` with a clear
human-readable message if correction is not possible.

Self-healing behaviours
-----------------------
* Symbols, sides, and order types are uppercased automatically.
* Leading/trailing whitespace is stripped.
* Commas in quantity/price strings are removed (e.g. "1,000" → "1000").

Usage:
    from bot.validators import validate_all
    params = validate_all(symbol="btcusdt", side="buy",
                          order_type="market", quantity="0.001")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bot.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


# ─── Result dataclass ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OrderParams:
    """Validated and normalised order parameters ready for the API layer.

    Attributes:
        symbol:     Trading pair, e.g. ``BTCUSDT``.
        side:       ``BUY`` or ``SELL``.
        order_type: ``MARKET`` or ``LIMIT``.
        quantity:   Positive float representing the order size.
        price:      Required for LIMIT orders; ``None`` for MARKET orders.
    """

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None


# ─── Individual validators ────────────────────────────────────────────────────


def validate_symbol(symbol: str) -> str:
    """Validate and heal a trading-pair symbol.

    Self-healing: strips whitespace and converts to uppercase.

    Args:
        symbol: Raw symbol string from the CLI, e.g. ``"btcusdt"``.

    Returns:
        Normalised uppercase symbol, e.g. ``"BTCUSDT"``.

    Raises:
        ValidationError: If the symbol is empty after normalisation.
    """
    original = symbol
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol cannot be empty", field="symbol",
                              hint="Provide a valid symbol, e.g. BTCUSDT")
    if symbol != original.strip().upper():
        logger.debug("Symbol auto-corrected: %r → %r", original, symbol)
    logger.debug("Symbol validated: %s", symbol)
    return symbol


def validate_side(side: str) -> str:
    """Validate and heal the order side.

    Self-healing: strips whitespace and converts to uppercase.

    Args:
        side: Raw side string, e.g. ``"buy"``.

    Returns:
        ``"BUY"`` or ``"SELL"``.

    Raises:
        ValidationError: If the normalised value is not in ``{BUY, SELL}``.
    """
    original = side
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{original!r}'. Must be BUY or SELL.",
            field="side",
            hint=f"Use one of: {', '.join(sorted(VALID_SIDES))}",
        )
    if side != original.strip().upper():
        logger.debug("Side auto-corrected: %r → %r", original, side)
    logger.debug("Side validated: %s", side)
    return side


def validate_order_type(order_type: str) -> str:
    """Validate and heal the order type.

    Self-healing: strips whitespace and converts to uppercase.

    Args:
        order_type: Raw type string, e.g. ``"limit"``.

    Returns:
        ``"MARKET"`` or ``"LIMIT"``.

    Raises:
        ValidationError: If the value is not a supported order type.
    """
    original = order_type
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{original!r}'. Must be MARKET or LIMIT.",
            field="type",
            hint=f"Use one of: {', '.join(sorted(VALID_ORDER_TYPES))}",
        )
    if order_type != original.strip().upper():
        logger.debug("Order type auto-corrected: %r → %r", original, order_type)
    logger.debug("Order type validated: %s", order_type)
    return order_type


def validate_quantity(quantity: str) -> float:
    """Validate the order quantity.

    Self-healing: removes commas (e.g. ``"1,000"`` → ``"1000"``).

    Args:
        quantity: Raw quantity string from the CLI.

    Returns:
        Positive float representing the quantity.

    Raises:
        ValidationError: If the value cannot be parsed or is not positive.
    """
    quantity = quantity.strip().replace(",", "")
    try:
        qty_float = float(quantity)
    except ValueError:
        raise ValidationError(
            f"Quantity '{quantity}' is not a valid number.",
            field="quantity",
            hint="Provide a positive numeric value, e.g. 0.001",
        )
    if qty_float <= 0:
        raise ValidationError(
            f"Quantity must be positive, got {qty_float}.",
            field="quantity",
            hint="Use a value greater than 0, e.g. 0.001",
        )
    logger.debug("Quantity validated: %s", qty_float)
    return qty_float


def validate_price(price: str | None, order_type: str) -> float | None:
    """Validate the order price.

    Self-healing: removes commas from price strings.

    Args:
        price:      Raw price string from the CLI, or ``None``.
        order_type: Already-validated order type (``"MARKET"`` or ``"LIMIT"``).

    Returns:
        Positive float for LIMIT orders; ``None`` for MARKET orders.

    Raises:
        ValidationError: If price is missing for a LIMIT order, cannot be
            parsed, or is not positive.
    """
    if order_type == "MARKET":
        if price is not None:
            logger.debug("Price ignored for MARKET order.")
        return None

    # LIMIT order – price is mandatory
    if price is None or price.strip() == "":
        raise ValidationError(
            "Price is required for LIMIT orders.",
            field="price",
            hint="Add --price <value>, e.g. --price 50000",
        )

    price = price.strip().replace(",", "")
    try:
        price_float = float(price)
    except ValueError:
        raise ValidationError(
            f"Price '{price}' is not a valid number.",
            field="price",
            hint="Provide a positive numeric value, e.g. 50000",
        )
    if price_float <= 0:
        raise ValidationError(
            f"Price must be positive, got {price_float}.",
            field="price",
            hint="Use a value greater than 0",
        )
    logger.debug("Price validated: %s", price_float)
    return price_float


# ─── Orchestrator ─────────────────────────────────────────────────────────────


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> OrderParams:
    """Validate all order parameters and return a clean ``OrderParams`` object.

    Calls each validator in sequence. The first failure raises a
    ``ValidationError`` immediately, giving the user a focused error message.

    Args:
        symbol:     Raw symbol string.
        side:       Raw side string.
        order_type: Raw order type string.
        quantity:   Raw quantity string.
        price:      Raw price string or ``None``.

    Returns:
        An :class:`OrderParams` with validated, normalised values.

    Raises:
        ValidationError: On the first parameter that fails validation.
    """
    logger.info("Validating order parameters …")
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)

    params = OrderParams(
        symbol=clean_symbol,
        side=clean_side,
        order_type=clean_type,
        quantity=clean_qty,
        price=clean_price,
    )
    logger.info("Validation passed: %s", params)
    return params
