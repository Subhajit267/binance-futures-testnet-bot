"""
------------------------------------------------------------
Author: Subhajit Halder
Module: Bot Core
File: bot/client.py

About:
    Low-level wrapper around the Binance Futures REST API.
    Handles HMAC-SHA256 request signing, timestamp injection,
    and HTTP communication. All other modules call this layer
    rather than constructing raw requests themselves.

    The client is intentionally thin: it signs and dispatches
    requests, parses the JSON response, and raises typed
    exceptions on API or network errors. Business logic
    (order building, formatting) lives in orders.py.

    Base URL defaults to the USDT-M Futures Testnet:
        https://testnet.binancefuture.com

Revisions:
    - 2026-05-19   Initial implementation; HMAC signing,
                   GET/POST helpers, BinanceAPIError
    - 2026-05-20   Added place_algo_order() and routed STOP_MARKET
                   orders to /fapi/v1/algoOrder per Binance API update.
------------------------------------------------------------
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

# ── Constants ─────────────────────────────────────────────────

BASE_URL    = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000   # Maximum allowed server-client clock skew (ms)


class BinanceAPIError(Exception):
    """
    Raised when the Binance API returns a non-200 application-level code.

    Attributes:
        code (int):    Binance error code (negative integer).
        message (str): Human-readable error description.
    """
    def __init__(self, code: int, message: str):
        self.code    = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """
    Authenticated Binance Futures REST client.

    All signed endpoints automatically receive a timestamp and
    recvWindow parameter before the HMAC signature is computed.
    A single requests.Session is reused for connection pooling.

    Args:
        api_key    (str): Binance API key.
        api_secret (str): Binance API secret.
        base_url   (str): Testnet or mainnet base URL.
    """

    def __init__(
        self,
        api_key:    str,
        api_secret: str,
        base_url:   str = BASE_URL,
    ):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.base_url   = base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY":  self.api_key,
            "Content-Type":  "application/x-www-form-urlencoded",
        })

        logger.info("BinanceClient ready (base_url=%s)", self.base_url)

    # ── Internal helpers ──────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject timestamp + recvWindow and append an HMAC-SHA256 signature.

        The signature is computed over the URL-encoded parameter string.
        Mutates and returns the same dict for convenience.

        Args:
            params (dict): Request parameters to sign.

        Returns:
            dict: Same dict with 'timestamp', 'recvWindow', and
                  'signature' keys added.
        """
        params["timestamp"]  = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW

        query     = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        params["signature"] = signature
        return params

    def _request(
        self,
        method:   str,
        endpoint: str,
        params:   Optional[Dict[str, Any]] = None,
        signed:   bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request and return the parsed JSON body.

        Logs the full request and response at DEBUG level. Raises
        typed exceptions for API errors and network failures so
        callers can handle them without inspecting raw responses.

        Args:
            method   (str):  HTTP verb ("GET" or "POST").
            endpoint (str):  Path component, e.g. "/fapi/v1/order".
            params   (dict): Query / body parameters.
            signed   (bool): If True, HMAC-sign before sending.

        Returns:
            dict: Parsed JSON response body.

        Raises:
            BinanceAPIError: API returned a non-200 application code.
            ConnectionError: Could not reach the server.
            TimeoutError:    Request exceeded the timeout.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.debug("REQUEST  %s %s  params=%s", method.upper(), url, params)

        try:
            resp = self.session.request(method, url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error: %s", exc)
            raise ConnectionError(
                f"Could not connect to {self.base_url}: {exc}"
            ) from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise TimeoutError("Request timed out.") from exc

        logger.debug(
            "RESPONSE %s %s  body=%s",
            resp.status_code, url, resp.text[:500],
        )

        data = resp.json()

        # Binance signals errors with a negative 'code' key
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            code = data.get("code", -1)
            msg  = data.get("msg", "Unknown error")
            logger.error("API error  code=%s  msg=%s", code, msg)
            raise BinanceAPIError(code, msg)

        return data

    # ── Public methods ────────────────────────────────────────

    def place_algo_order(self, **kwargs) -> Dict[str, Any]:
        """
        Submit a new algorithmic (conditional) order.
        Required for STOP_MARKET, TAKE_PROFIT_MARKET, etc.
        """
        # Set a default for the new 'algoType' parameter
        kwargs.setdefault("algoType", "CONDITIONAL")
        return self._request("POST", "/fapi/v1/algoOrder", params=kwargs, signed=True)

    def get_server_time(self) -> int:
        """
        Fetch the Binance server timestamp.

        Returns:
            int: Server time in milliseconds since epoch.
        """
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def get_account_info(self) -> Dict[str, Any]:
        """
        Retrieve account balance and position information.

        Returns:
            dict: Full account info response from /fapi/v2/account.
        """
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        Submit a new futures order.

        STOP_MARKET orders are routed to /fapi/v1/algoOrder (Algo API).
        All other types use /fapi/v1/order. Keyword arguments are forwarded
        directly; the caller is responsible for supplying all required fields.

        Returns:
            dict: Order response containing orderId (or algoId) and details.
        """
        # Route STOP_MARKET orders to the new Algo Order endpoint
        if kwargs.get("type") == "STOP_MARKET":
            return self.place_algo_order(**kwargs)

        return self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)