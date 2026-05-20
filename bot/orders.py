"""
------------------------------------------------------------
Author: Subhajit Halder
Module: Bot Core
File: bot/orders.py

About:
    Order placement logic and response formatting.
    Constructs the correct parameter dict for each order type,
    delegates the HTTP call to BinanceClient, and formats the
    response into a readable terminal summary.

    Supported order types:
      MARKET     — executes immediately at best available price
      LIMIT      — rests in the order book at a specified price (GTC)
      STOP_MARKET — triggers a MARKET order when triggerPrice is reached

Revisions:
    - 2026-05-19   Initial implementation; MARKET + LIMIT
    - 2026-05-19   Added STOP_MARKET as bonus order type
    - 2026-05-20   Updated STOP_MARKET to use Algo API parameters:
                   triggerPrice, workingType (instead of stopPrice)
------------------------------------------------------------
"""

from typing import Any, Dict, Optional

from .client import BinanceClient
from .logging_config import get_logger

logger = get_logger("orders")


# ------------------------------- Parameter builder -------------------------------

def _build_order_params(
    symbol:     str,
    side:       str,
    order_type: str,
    quantity:   str,
    price:      Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct the Binance API parameter dict for a given order type.

    LIMIT orders receive a 'price' and 'timeInForce' (GTC).
    STOP_MARKET orders receive 'triggerPrice' and 'workingType' for the Algo API.
    MARKET orders need only symbol, side, type, and quantity.

    Args:
        symbol     (str):      Trading pair, e.g. "BTCUSDT".
        side       (str):      "BUY" or "SELL".
        order_type (str):      "MARKET", "LIMIT", or "STOP_MARKET".
        quantity   (str):      Order quantity as a decimal string.
        price      (str|None): Limit price or stop trigger price.

    Returns:
        dict: Parameter dict ready to be passed to BinanceClient.place_order().
    """
    params: Dict[str, Any] = {
        "symbol":   symbol,
        "side":     side,
        "type":     order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        params["price"]       = price
        params["timeInForce"] = "GTC"

    if order_type == "STOP_MARKET":
        # Algo Order API parameters (replaces the old stopPrice approach)
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "triggerPrice": price,       # The price that triggers the order
            "workingType": "MARK_PRICE"  # Other options: CONTRACT_PRICE
        }
        return params

    return params


# ------------------------------- Placement -------------------------------

def place_order(
    client:     BinanceClient,
    symbol:     str,
    side:       str,
    order_type: str,
    quantity:   str,
    price:      Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build and submit a futures order, returning the Binance response.

    Logs the intent before sending and the outcome (orderId/algoId, status,
    executedQty, avgPrice) after a successful response.

    Args:
        client     (BinanceClient): Authenticated API client.
        symbol     (str):           Trading pair, e.g. "BTCUSDT".
        side       (str):           "BUY" or "SELL".
        order_type (str):           "MARKET", "LIMIT", or "STOP_MARKET".
        quantity   (str):           Order quantity.
        price      (str|None):      Limit / stop price (None for MARKET).

    Returns:
        dict: Raw Binance order response.

    Raises:
        BinanceAPIError: Propagated from BinanceClient on API failure.
        ConnectionError: Propagated on network failure.
    """
    params = _build_order_params(symbol, side, order_type, quantity, price)

    logger.info(
        "Placing %s %s order  symbol=%s  qty=%s  price=%s",
        side, order_type, symbol, quantity, price or "N/A",
    )

    response = client.place_order(**params)

    # For STOP_MARKET orders, the response uses 'algoId' instead of 'orderId'
    order_id = response.get("orderId") or response.get("algoId")
    logger.info(
        "Order placed  orderId=%s  status=%s  executedQty=%s  avgPrice=%s",
        order_id,
        response.get("status"),
        response.get("executedQty", "0"),
        response.get("avgPrice", "N/A"),
    )

    return response


# ------------------------------- Formatting -------------------------------

def format_order_response(response: Dict[str, Any]) -> str:
    """
    Format a Binance order response dict into a readable terminal block.

    Handles both regular orders (orderId) and algo orders (algoId).

    Args:
        response (dict): Order response as returned by place_order().

    Returns:
        str: Multi-line formatted string ready to print.
    """
    # Use algoId if present, otherwise orderId
    order_id = response.get("orderId") or response.get("algoId", "N/A")
    # For algo orders, stopPrice might not exist; use triggerPrice if present
    stop_price = response.get("stopPrice") or response.get("triggerPrice", "N/A")

    lines = [
        "",
        " ----------------------------------------- ",
        "|           ORDER RESPONSE DETAILS        |",
        " ----------------------------------------- ",
        f"  Order ID     : {order_id}",
        f"  Symbol       : {response.get('symbol',      'N/A')}",
        f"  Side         : {response.get('side',        'N/A')}",
        f"  Type         : {response.get('type',        'N/A')}",
        f"  Status       : {response.get('status',      'N/A')}",
        f"  Orig Qty     : {response.get('origQty',     'N/A')}",
        f"  Executed Qty : {response.get('executedQty', 'N/A')}",
        f"  Avg Price    : {response.get('avgPrice',    'N/A')}",
        f"  Limit Price  : {response.get('price',       'N/A')}",
        f"  Stop/Trigger Price: {stop_price}",
        f"  Time in Force: {response.get('timeInForce', 'N/A')}",
        f"  Updated At   : {response.get('updateTime',  'N/A')}",
    ]
    return "\n".join(lines)
