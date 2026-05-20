<div align="center">

# 💹 Binance Futures Testnet Trading Bot

*A structured Python CLI application for placing orders on Binance Futures Testnet (USDT-M)*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Binance](https://img.shields.io/badge/Binance-Futures%20Testnet-yellow?logo=binance)](https://testnet.binancefuture.com)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)]()
[![Status](https://img.shields.io/badge/Status-Complete-brightgreen)]()

</div>

---

## 📖 Overview

**Binance Futures Trading Bot** is a clean, modular Python application that interacts with the Binance Futures Testnet REST API to place and manage futures orders programmatically via the command line.

The bot supports all core order types required for USDT-M perpetual futures trading — **MARKET**, **LIMIT**, and **STOP_MARKET** — with full input validation, structured logging, and typed exception handling at every layer.

The codebase is organized into a clean separation of concerns:
- **`bot/client.py`** handles all HTTP communication and HMAC-SHA256 signing.
- **`bot/orders.py`** contains order-building logic and response formatting.
- **`bot/validators.py`** validates every CLI argument before any API call is made.
- **`cli.py`** is the thin entry point that wires everything together.

---

## ✨ Features

- **MARKET orders** — execute instantly at best available price
- **LIMIT orders** — rest in the order book at a specified price (GTC)
- **STOP_MARKET orders** — trigger a market order when stop price is reached *(bonus)*
- **BUY and SELL** sides supported for all order types
- **Full CLI** via `argparse` with clear validation messages
- **Dual logging** — DEBUG to file, INFO to console, both structured
- **Typed exceptions** — API errors, network failures, and validation errors handled separately
- **`.env`-based credentials** — no hardcoded keys anywhere in the codebase

---

## 🏗️ Architecture

```
cli.py
  └── validates input (validators.py)
  └── builds order params (orders.py)
        └── calls REST API (client.py)
              └── signs request (HMAC-SHA256)
              └── sends HTTP POST to testnet
              └── parses and returns response
  └── formats and prints response (orders.py)
  └── logs everything (logging_config.py)
```

---

## 🧱 System Modules

```
bot/
├── client.py          – Binance REST API wrapper; HMAC signing, request dispatch, error handling
├── orders.py          – Order parameter builder, placement logic, response formatter
├── validators.py      – Input validation for symbol, side, type, quantity, and price
└── logging_config.py  – Dual-handler logger (file DEBUG + console INFO)
```

---

## 📁 File Structure

```
trading_bot/
│   cli.py                  – CLI entry point (argparse sub-commands)
│   requirements.txt
│   .env.example
│   README.md
│
├── bot/
│   ├── __init__.py
│   ├── client.py
│   ├── orders.py
│   ├── validators.py
│   └── logging_config.py
│
└── logs/
    └── trading_bot.log     – All API requests, responses, and errors
```

---

## ⚙️ Installation

### 1. Clone or extract the project

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading_bot
```

Or extract the zip and `cd` into the folder.

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate — Windows:
venv\Scripts\activate

# Activate — Linux / Mac:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Get your API key and secret from [testnet.binancefuture.com](https://testnet.binancefuture.com) → log in with GitHub → click **API Key** → generate.

```bash
# Windows:
copy .env.example .env

# Linux / Mac:
cp .env.example .env
```

Open `.env` in any text editor and fill in:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_key_here
```

No quotes. No spaces around `=`.

---

## 🚀 Usage

### MARKET order

```bash
# BUY 0.01 BTC at current market price
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# SELL 0.5 ETH at current market price
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.5
```

### LIMIT order

```bash
# BUY 0.01 BTC — waits until price drops to $10,000
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 10000

# SELL 0.01 BTC — waits until price rises to $99,999
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 99999
```

### STOP_MARKET order *(bonus)*

```bash
# Triggers a BUY market order when ETH hits $4,000
python cli.py place --symbol ETHUSDT --side BUY --type STOP_MARKET --quantity 0.1 --price 4000
```

> **Note:** Stop price must be within ~10% of the current market price or Binance will reject it.

### Verbose / debug output

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

---

## 📟 Command Reference

| Flag | Required | Description |
|------|----------|-------------|
| `--symbol` | ✔ | Trading pair, e.g. `BTCUSDT`, `ETHUSDT` |
| `--side` | ✔ | `BUY` or `SELL` |
| `--type` | ✔ | `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `--quantity` | ✔ | Order size, e.g. `0.01` |
| `--price` | LIMIT / STOP | Limit price or stop trigger price |
| `--log-level` | ✗ | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |

---

## 📊 Sample Output

```
 --------------------------------------------------
|    Binance Futures Testnet Trading Bot v1.0      |
|    USDT-M Perpetuals                             |
 --------------------------------------------------

── Order Request Summary ──────────────────────────
  Symbol    : BTCUSDT
  Side      : BUY
  Type      : MARKET
  Quantity  : 0.01
───────────────────────────────────────────────────

⏳ Submitting order …

┌─────────────────────────────────────────┐
│           ORDER RESPONSE DETAILS        │
└─────────────────────────────────────────┘
  Order ID     : 13167500236
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : NEW
  Orig Qty     : 0.0100
  Executed Qty : 0.0000
  Avg Price    : 0.00
  Limit Price  : 0.00
  Stop Price   : 0.00
  Time in Force: GTC
  Updated At   : 1779275183897

✔ Order placed successfully!
```

---

## 🐞 Error Handling

| Scenario | Exit Code | Message |
|----------|-----------|---------|
| Missing `--price` on LIMIT / STOP_MARKET | `1` | Validation error |
| Invalid symbol, side, or order type | `1` | Validation error |
| Binance API error (bad key, margin, etc.) | `2` | API error with code |
| Network or timeout failure | `3` | Network error |
| Unexpected exception | `4` | Logged with traceback |

---

## 📁 File Storage

| File | Purpose |
|------|---------|
| `.env` | API credentials (never committed to git) |
| `logs/trading_bot.log` | All requests, responses, and errors |

---

## 🐞 Known Issues

- MARKET orders on testnet sometimes return `status: NEW` instead of `FILLED` — this is a testnet quirk, not a bot error; the order was accepted
- Stop price must be near current market price or Binance returns error `-4120`
- Terminal colour rendering may vary on older Windows consoles

---

## 🛤 Future Roadmap

- OCO (One-Cancels-the-Other) order support
- Interactive menu mode (no flags needed)
- Order status polling and cancellation
- WebSocket live price feed integration
- Lightweight web dashboard

---

## 📄 Assumptions

- Only **USDT-M perpetual futures** on the testnet are targeted
- `timeInForce` is set to `GTC` for all LIMIT orders
- Credentials are loaded from `.env` or the system environment
- One-Way position mode (Hedge OFF) is assumed — the testnet default
- Quantity precision is passed as-is; adjust if the testnet rejects with a lot-size error

---

## Requirements

- Python 3.8+
- `requests` — HTTP client
- `python-dotenv` — `.env` file loader

---

<div align="center">

### **Subhajit Halder**

📧 [subhajithalder267@outlook.com](mailto:subhajithalder267@outlook.com)

*Department of Information Technology*  
*Jalpaiguri Government Engineering College*

</div>
