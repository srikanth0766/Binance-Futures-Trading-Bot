# Binance Futures Testnet Trading Bot

A full-stack trading bot for the **Binance Futures Testnet** (USDT-M perpetual contracts). It consists of a robust **Python CLI** with self-healing error handling, a **FastAPI REST server**, and a sleek **React + TypeScript UI** — all running locally.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Quick Start (CLI only)](#quick-start-cli-only)
4. [Quick Start (UI + API)](#quick-start-ui--api)
5. [Getting Testnet API Keys](#getting-testnet-api-keys)
6. [Configuration (.env)](#configuration-env)
7. [CLI Reference](#cli-reference)
8. [Running Tests](#running-tests)
9. [UI Reference](#ui-reference)
10. [Error Handling & Self-Healing](#error-handling--self-healing)
11. [Assumptions & Limitations](#assumptions--limitations)

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── config.py            # Settings loader (.env → frozen dataclass)
│   ├── logging_config.py    # Dual-output rotating logger
│   ├── exceptions.py        # Typed exception hierarchy
│   ├── validators.py        # Input validation + self-healing
│   ├── client.py            # HTTP client (HMAC signing + retry)
│   ├── orders.py            # Order placement logic
│   ├── formatters.py        # ANSI terminal output formatter
│   └── health.py            # Pre-flight connectivity checker
├── frontend/                # React + TypeScript UI (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── OrderForm.tsx       # Trade form (symbol, side, type, qty, price)
│   │   │   └── TradeConsole.tsx    # Live execution log panel
│   │   ├── App.tsx                 # Root component + state management
│   │   ├── api.ts                  # Fetch wrapper for FastAPI backend
│   │   ├── types.ts                # TypeScript interfaces
│   │   └── index.css               # Full dark-glassmorphism design system
│   └── package.json
├── tests/
│   ├── test_market_order.py  # Integration test – MARKET orders
│   └── test_limit_order.py   # Integration test – LIMIT orders
├── logs/
│   └── trading_bot.log       # Auto-created at runtime
├── cli.py                    # CLI entry point (argparse)
├── server.py                 # FastAPI REST server (backend for UI)
├── requirements.txt
├── .env.example              # Environment variable template
└── .gitignore
```

---

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** and **npm** (for the React UI only)
- A **Binance Futures Testnet** account and API keys (see below)

---

## Quick Start (CLI only)

```bash
# 1. Clone the repository
git clone https://github.com/srikanth0766/Binance-Futures-Trading-Bot.git
cd Binance-Futures-Trading-Bot/trading_bot

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up your environment file
cp .env.example .env
# Open .env and fill in your testnet API credentials (see section below)

# 5. Place a MARKET BUY order
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.01
```

---

## Quick Start (UI + API)

This runs the full-stack app — a FastAPI backend and a React frontend.

### Terminal 1 – Start the API server

```bash
cd trading_bot
source venv/bin/activate
python3 server.py
# → API running at http://localhost:8000
```

### Terminal 2 – Start the React UI

```bash
cd trading_bot/frontend
npm install         # only needed the first time
npm run dev
# → UI running at http://localhost:5173
```

Open **http://localhost:5173** in your browser. Select your order parameters, click **BUY** or **SELL**, and see the result in the Execution Log panel.

---

## Getting Testnet API Keys

1. Go to **https://testnet.binancefuture.com**
2. Log in (or create a free account)
3. Navigate to **API Management** in the top-right menu
4. Click **Create API** — copy the **API Key** and **Secret Key** immediately (the secret is only shown once)
5. Paste both into your `.env` file (see below)

> ⚠️ These are **testnet-only** keys and carry no financial risk. Never use mainnet keys with this project.

---

## Configuration (.env)

Copy `.env.example` to `.env` and fill in your values:

```env
# Required – from Binance Futures Testnet → API Management
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here

# Optional – defaults shown
BASE_URL=https://testnet.binancefuture.com
RECV_WINDOW=5000
LOG_LEVEL=DEBUG
```

> **Never commit your `.env` file.** It is listed in `.gitignore`.

---

## CLI Reference

All commands are run from inside the `trading_bot/` directory with the venv active.

### Place a MARKET order

```bash
# BUY 0.01 BTC at market price (notional > 100 USDT required)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.01

# SELL 0.01 BTC at market price
python cli.py --symbol BTCUSDT --side SELL --type MARKET --qty 0.01
```

### Place a LIMIT order

```bash
# SELL LIMIT at 150,000 USDT
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.01 --price 150000

# BUY LIMIT at 50,000 USDT
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --qty 0.01 --price 50000
```

### Self-healing inputs

```bash
# Lowercase inputs are auto-corrected
python cli.py --symbol btcusdt --side buy --type market --qty 0.01
```

### Full argument reference

```
usage: trading_bot [-h] --symbol SYMBOL --side {BUY,SELL}
                   --type {MARKET,LIMIT} --qty QUANTITY
                   [--price PRICE] [--log-dir DIR]

  --symbol, -s   Trading pair (e.g. BTCUSDT)
  --side         BUY or SELL
  --type, -t     MARKET or LIMIT
  --qty, -q      Quantity in base asset units (e.g. 0.01)
  --price, -p    Limit price in USDT (required for LIMIT orders)
  --log-dir      Custom log directory (default: ./logs/)
```

### Exit codes

| Code | Meaning                  |
|------|--------------------------|
| `0`  | Success                  |
| `1`  | Validation / config error|
| `2`  | Binance API error        |
| `3`  | Network error            |

---

## Running Tests

Integration tests require valid `.env` credentials and a live connection to the testnet.

```bash
# From inside trading_bot/ with venv active
pip install pytest       # only needed once

# Run all tests
python -m pytest tests/ -v

# Run individually
python -m pytest tests/test_market_order.py -v
python -m pytest tests/test_limit_order.py -v
```

---

## UI Reference

The React UI at **http://localhost:5173** provides:

| Control              | Description                                      |
|----------------------|--------------------------------------------------|
| **Order Side**       | Segmented BUY / SELL toggle (colour-coded green/red) |
| **Order Type**       | MARKET or LIMIT toggle                           |
| **Trading Pair**     | Symbol input (e.g. `BTCUSDT`), auto-uppercased   |
| **Quantity**         | Numeric input — minimum notional > 100 USDT      |
| **Limit Price**      | Shown only when LIMIT is selected                |
| **BUY / SELL button**| Submits the order; shows spinner while pending   |
| **Execution Log**    | Live panel — shows submission, success with order ID & status, or error |

---

## Error Handling & Self-Healing

### Level 1 – Input Healing (`validators.py`)

| Problem                  | Auto Fix                              |
|--------------------------|---------------------------------------|
| `"btcusdt"` symbol       | → `"BTCUSDT"` (uppercased)           |
| `"buy"` side             | → `"BUY"`                            |
| `"1,000"` quantity       | → `1000.0` (comma stripped)          |
| Missing price for LIMIT  | → Exit 1 with clear hint             |

### Level 2 – Network Healing (`client.py`)

| Failure                       | Response                                     |
|-------------------------------|----------------------------------------------|
| Timeout / connection reset    | Retry ×3 with 1s → 2s → 4s backoff + jitter |
| Binance 5xx server error      | Retry ×3                                    |

### Level 3 – API Error Hints (`exceptions.py`)

| Binance Error Code | Auto Hint                                              |
|--------------------|--------------------------------------------------------|
| `-1121`            | "Check symbol format – use uppercase e.g. BTCUSDT"   |
| `-2019`            | "Reduce quantity or deposit more funds"               |
| `-1013`            | "Check LOT_SIZE filter: adjust quantity to allowed step size" |
| `-4164`            | Order notional too small – increase quantity           |

---

## Assumptions & Limitations

- **Testnet only** – `BASE_URL` defaults to `https://testnet.binancefuture.com`. Do not use real API credentials with this project.
- **Minimum notional** – Binance enforces a minimum order value of **100 USDT**. For BTCUSDT at ~$80,000, the minimum safe quantity is **0.01 BTC**.
- **Default `timeInForce=GTC`** for LIMIT orders (Good Till Cancelled).
- **No position management** – the bot places orders but does not track open positions or PnL.
- **Python 3.9+** required for `dict[str, Any]` inline type hints.
- **UI requires both servers** – the React frontend at port 5173 depends on the FastAPI server at port 8000.
