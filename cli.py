"""
------------------------------------------------------------
Author: Subhajit Halder
Module: Entry Point
File: cli.py

About:
    Command-line interface for the Binance Futures Testnet
    trading bot.  Parses and validates user arguments, loads
    API credentials from the environment (or a .env file),
    then delegates to the bot layer to place the order.

    Sub-commands:
        place   Place a MARKET, LIMIT, or STOP_MARKET order.

    Usage examples:
        python cli.py place --symbol BTCUSDT --side BUY  \\
                            --type MARKET --quantity 0.01

        python cli.py place --symbol BTCUSDT --side SELL \\
                            --type LIMIT  --quantity 0.01 --price 68000

        python cli.py place --symbol ETHUSDT --side BUY  \\
                            --type STOP_MARKET --quantity 0.1 --price 2500

        python cli.py --log-level DEBUG place --symbol BTCUSDT \\
                            --side BUY --type MARKET --quantity 0.01

Revisions:
    - 2026-05-19   Initial implementation
------------------------------------------------------------
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client     import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logging
from bot.orders     import format_order_response, place_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

load_dotenv()


# ── Display helpers ───────────────────────────────────────────

def _print_banner():
    """Print the application title banner."""
    print(
        "\n"
        " --------------------------------------------------\n"
        "|    Binance Futures Testnet Trading Bot v1.0      |\n"
        "|    USDT-M Perpetuals                             |\n"
        " --------------------------------------------------"
    )


def _print_order_summary(symbol, side, order_type, quantity, price):
    """
    Print a pre-submission summary of the requested order.

    Args:
        symbol     (str):      Trading pair.
        side       (str):      BUY or SELL.
        order_type (str):      MARKET, LIMIT, or STOP_MARKET.
        quantity   (str):      Order quantity.
        price      (str|None): Limit / stop price, or None.
    """
    label = "Stop Price" if order_type == "STOP_MARKET" else "Price"

    print("\n── Order Request Summary ──────────────────────────")
    print(f"  Symbol    : {symbol}")
    print(f"  Side      : {side}")
    print(f"  Type      : {order_type}")
    print(f"  Quantity  : {quantity}")
    if price:
        print(f"  {label:<10}: {price}")
    print("───────────────────────────────────────────────────")


# ── Command handler ───────────────────────────────────────────

def cmd_place(args):
    """
    Handle the 'place' sub-command end-to-end.

    Validates CLI inputs, loads credentials, prints a summary,
    submits the order, and prints the result. Exits with a
    non-zero code on any error so the caller can detect failure.

    Exit codes:
        1  Validation error (bad input)
        2  Binance API error
        3  Network / timeout error
        4  Unexpected error

    Args:
        args (argparse.Namespace): Parsed CLI arguments.
    """
    setup_logging(args.log_level)

    # ── Validate inputs ───────────────────────────────────────
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.type)
        quantity   = validate_quantity(args.quantity)
        price      = validate_price(args.price, order_type)
    except ValidationError as exc:
        print(f"\n✘ Validation error: {exc}")
        sys.exit(1)

    # ── Load credentials ──────────────────────────────────────
    api_key    = os.getenv("BINANCE_API_KEY",    "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n✘ Missing API credentials.\n"
            "   Set BINANCE_API_KEY and BINANCE_API_SECRET in .env "
            "or in the environment."
        )
        sys.exit(1)

    # ── Submit ────────────────────────────────────────────────
    _print_banner()
    _print_order_summary(symbol, side, order_type, quantity, price)
    print("\n⏳ Submitting order …\n")

    client = BinanceClient(api_key, api_secret)

    try:
        response = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        print(format_order_response(response))
        print("\n✔ Order placed successfully!\n")

    except BinanceAPIError as exc:
        print(f"\n✘ Binance API error [{exc.code}]: {exc.message}")
        sys.exit(2)

    except (ConnectionError, TimeoutError) as exc:
        print(f"\n✘ Network error: {exc}")
        sys.exit(3)

    except Exception as exc:
        print(f"\n✘ Unexpected error: {exc}")
        sys.exit(4)


# ── Argument parser ───────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    """
    Construct the top-level argument parser with sub-commands.

    Returns:
        argparse.ArgumentParser: Fully configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot — USDT-M",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── 'place' sub-command ───────────────────────────────────
    place = subparsers.add_parser("place", help="Place a futures order")
    place.add_argument("--symbol",   required=True,
                       help="Trading pair, e.g. BTCUSDT")
    place.add_argument("--side",     required=True,
                       help="BUY or SELL")
    place.add_argument("--type",     required=True, dest="type",
                       help="MARKET, LIMIT, or STOP_MARKET")
    place.add_argument("--quantity", required=True,
                       help="Order quantity")
    place.add_argument("--price",    default=None,
                       help="Limit / stop price (required for LIMIT and STOP_MARKET)")
    place.set_defaults(func=cmd_place)

    return parser


# ── Entry point ───────────────────────────────────────────────

def main():
    """Parse arguments and dispatch to the appropriate command handler."""
    parser = _build_parser()
    args   = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
