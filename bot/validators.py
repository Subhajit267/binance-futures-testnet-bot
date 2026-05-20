"""
------------------------------------------------------------
Author: Subhajit Halder
Module: Bot Core
File: bot/validators.py

About:
    Input validation for all CLI-supplied order parameters.
    Every public function either returns the cleaned/normalised
    value on success or raises ValidationError with a clear
    human-readable message.

Revisions:
    - 2026-05-19   Initial implementation; MARKET + LIMIT
    - 2026-05-19   Added STOP_MARKET as bonus order type
------------------------------------------------------------
"""

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES       = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    """Raised when a CLI argument fails a validation check."""
    pass


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.isalnum():
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric, e.g. BTCUSDT."
        )
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}."
        )
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}."
        )
    return t


def validate_quantity(quantity: str) -> str:
    try:
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValidationError(
                f"Quantity must be greater than 0. Got: {quantity}"
            )
        return str(qty)
    except InvalidOperation:
        raise ValidationError(
            f"Invalid quantity '{quantity}'. Must be a positive number."
        )


def validate_price(price: Optional[str], order_type: str) -> Optional[str]:
    if order_type == "MARKET":
        return None

    label = "Stop price" if order_type == "STOP_MARKET" else "Price"

    if price is None:
        if order_type == "STOP_MARKET":
            raise ValidationError(
                f"{label} is required for STOP_MARKET orders. "
                "Use a price within ~10% of current market price."
            )
        raise ValidationError(
            f"{label} is required for {order_type} orders."
        )

    try:
        p = Decimal(str(price))
        if p <= 0:
            raise ValidationError(
                f"{label} must be greater than 0. Got: {price}"
            )
        return str(p)
    except InvalidOperation:
        raise ValidationError(
            f"Invalid {label.lower()} '{price}'. Must be a positive number."
        )
