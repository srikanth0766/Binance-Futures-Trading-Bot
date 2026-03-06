# Binance Futures Testnet Trading Bot

A clean, modular Python CLI application that places **MARKET** and **LIMIT** orders on the
Binance Futures Testnet (USDT-M perpetual) with structured logging, typed error handling,
and a self-healing fault-tolerance layer.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
4. [How to Run](#how-to-run)
5. [How to Test](#how-to-test)
6. [Logging](#logging)
7. [Error Handling & Self-Healing](#error-handling--self-healing)
8. [Assumptions & Limitations](#assumptions--limitations)

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── config.py            # Module 5  – Settings loader (.env → frozen dataclass)
│   ├── logging_config.py    # Module 2  – Dual-output rotating logger
│   ├── exceptions.py        # Module 3  – Typed exception hierarchy
│   ├── validators.py        # Module 4  – Input validation + self-healing
│   ├── client.py            # Module 6  – HTTP client (HMAC signing + retry)
│   ├── orders.py            # Module 7  – Order placement logic
│   ├── formatters.py        # Module 8  – ANSI terminal output formatter
│   └── health.py            # Module 9  – Pre-flight connectivity checker
├── tests/
│   ├── __init__.py
│   ├── test_market_order.py # Integration test for MARKET orders
│   └── test_limit_order.py  # Integration test for LIMIT orders
├── logs/
│   └── trading_bot.log      # Auto-created at runtime
├── cli.py                   # Module 10 – CLI entry point (argparse)
├── agents.md                # Architecture + agent blueprint
├── .env.example             # Environment variable template
├── .gitignore
└── requirements.txt
```

---

## Prerequisites

- Python **3.9+**
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account
- Testnet API key + secret (generated in the testnet dashboard under **API Management**)

---

## Setup

```bash
# 1. Clone / download the project
cd trading_bot

# 2. (Recommended) Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Open .env and fill in:
#   BINANCE_API_KEY=your_testnet_api_key
#   BINANCE_SECRET_KEY=your_testnet_secret_key
```

> **Never commit your `.env` file.** It is listed in `.gitignore`.

---

## How to Run

All commands are run from inside the `trading_bot/` directory.

### Place a MARKET order

```bash
# BUY 0.001 BTC at market price
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

# SELL 0.001 BTC at market price
python cli.py --symbol BTCUSDT --side SELL --type MARKET --qty 0.001
```

### Place a LIMIT order

```bash
# SELL LIMIT at 150,000 USDT (rests on the book if above market)
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 150000

# BUY LIMIT at 50,000 USDT
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --qty 0.001 --price 50000
```

### Self-healing inputs (case-insensitive)

```bash
# Lowercase inputs are automatically corrected – no error raised
python cli.py --symbol btcusdt --side buy --type market --qty 0.001
```

### Full argument reference

```
usage: trading_bot [-h] --symbol SYMBOL --side {BUY,SELL} --type {MARKET,LIMIT}
                   --qty QUANTITY [--price PRICE] [--log-dir DIR]

optional arguments:
  --symbol, -s   Trading pair (e.g. BTCUSDT)
  --side         BUY or SELL
  --type, -t     MARKET or LIMIT
  --qty, -q      Quantity in base asset units (e.g. 0.001)
  --price, -p    Limit price in USDT (required for LIMIT orders)
  --log-dir      Custom log directory (default: ./logs/)
```

### Exit codes

| Code | Meaning              |
|------|----------------------|
| `0`  | Success              |
| `1`  | Validation / config error |
| `2`  | Binance API error    |
| `3`  | Network error        |

---

## How to Test

```bash
# From inside trading_bot/
pip install pytest          # only needed once

# Run all integration tests (requires valid .env keys)
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_market_order.py -v
python -m pytest tests/test_limit_order.py -v
```

> The tests invoke `cli.py` as a subprocess and validate exit codes + log content.

---

## Logging

Logs are written to `logs/trading_bot.log` (rotating, max 5 MB, 3 backups).

| Channel | Level  | Content                                         |
|---------|--------|-------------------------------------------------|
| File    | DEBUG  | Full request params (signature masked), responses |
| Console | INFO   | Order events, health check results, errors      |

Sample log output:

```
2026-03-06 16:44:00 | INFO     | root | Logging initialised → logs/trading_bot.log
2026-03-06 16:44:00 | INFO     | root | Settings loaded: base_url=https://testnet.binancefuture.com ...
2026-03-06 16:44:00 | INFO     | bot.validators | Validation passed: OrderParams(symbol='BTCUSDT', ...)
2026-03-06 16:44:00 | INFO     | bot.health | Running pre-flight health checks …
2026-03-06 16:44:00 | DEBUG    | bot.client | → POST https://testnet.binancefuture.com/fapi/v1/order params={...}
2026-03-06 16:44:01 | DEBUG    | bot.client | ← HTTP 200  body={"orderId":123456, "status":"FILLED", ...}
2026-03-06 16:44:01 | INFO     | bot.orders | MARKET order placed: orderId=123456 status=FILLED executedQty=0.001
```

---

## Error Handling & Self-Healing

### Level 1 – Input Healing (validators.py)
| Input Problem | Automatic Fix |
|---------------|---------------|
| `"btcusdt"` | → `"BTCUSDT"` (uppercased) |
| `"buy"` | → `"BUY"` |
| `"1,000"` quantity | → `1000.0` (comma stripped) |
| Missing `--price` for LIMIT | → exit 1 with clear hint |

### Level 2 – Network Healing (client.py)
| Failure | Response |
|---------|----------|
| Timeout / connection reset | Retry ×3 with 1s → 2s → 4s backoff + ±0.5s jitter |
| Binance 5xx server error | Retry ×3 |

### Level 3 – API Healing (exceptions.py)
| Binance Error Code | Auto Hint |
|--------------------|-----------|
| `-1121` Invalid symbol | "Check symbol format – use uppercase e.g. BTCUSDT" |
| `-2019` Insufficient margin | "Reduce quantity or deposit more funds" |
| `-1013` Invalid qty | "Check LOT_SIZE filter: adjust quantity to allowed step size" |

---

## Assumptions & Limitations

- **Testnet only** – `BASE_URL` defaults to `https://testnet.binancefuture.com`. Do not change this to mainnet without also configuring real API credentials and understanding financial risk.
- **Default `timeInForce=GTC`** for LIMIT orders (Good Till Cancelled).
- **No position management** – the bot places orders but does not track open positions or PnL.
- **Quantity precision** – Binance enforces LOT_SIZE filters. If you get a `-1013` error, halve the quantity or check the symbol's filter rules in the testnet web UI.
- **Python 3.9+** required for `dict[str, Any]` type hints used inline.
