"""
------------------------------------------------------------
Author: Subhajit Halder
Module: Bot Core
File: bot/logging_config.py

About:
    Configures structured logging for the trading bot.
    Writes DEBUG-level records to a rotating log file and
    INFO-level records to the console. Both handlers use a
    consistent timestamp + level + module format so log
    files are easy to grep and diff.

    All other modules obtain their logger via get_logger(),
    which returns a child of the root "trading_bot" logger
    so that the file and console handlers are inherited
    automatically.

Revisions:
    - 2026-05-19   Initial implementation
------------------------------------------------------------
"""

import logging
import sys
from pathlib import Path

LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Create and configure the root trading_bot logger.

    Attaches two handlers:
      - FileHandler (DEBUG) → logs/trading_bot.log
      - StreamHandler (INFO or as specified) → stdout

    Args:
        log_level (str): Minimum level for console output.
                         File always receives DEBUG.

    Returns:
        logging.Logger: Configured root logger.
    """
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # ── File handler (DEBUG + full timestamp) ─────────────────
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)

    # ── Console handler (INFO, short timestamp) ────────────────
    console_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a named child logger under the trading_bot hierarchy.

    Args:
        name (str): Module-level identifier, e.g. "client" or "orders".

    Returns:
        logging.Logger: Child logger that inherits all root handlers.
    """
    return logging.getLogger(f"trading_bot.{name}")
