"""
tests/test_limit_order.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Integration test – LIMIT order on Binance Futures Testnet.

Invokes ``cli.py`` as a subprocess to simulate real usage and verify:
  • The command exits with code 0.
  • A log file contains LIMIT-order-specific keywords.

Prerequisites:
  • Valid ``BINANCE_API_KEY`` and ``BINANCE_SECRET_KEY`` in ``.env``.
  • A network connection to https://testnet.binancefuture.com.

Run:
    cd trading_bot
    python -m pytest tests/test_limit_order.py -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_limit_sell_order():
    """Place a LIMIT SELL and assert exit 0 + log written with LIMIT keywords."""
    result = subprocess.run(
        [
            sys.executable, "cli.py",
            "--symbol", "BTCUSDT",
            "--side",   "SELL",
            "--type",   "LIMIT",
            "--qty",    "0.001",
            "--price",  "150000",   # Far above market – rests as open order
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    assert result.returncode == 0, (
        f"Expected exit code 0, got {result.returncode}.\n"
        f"STDERR: {result.stderr}"
    )

    log_path = PROJECT_ROOT / "logs" / "trading_bot.log"
    assert log_path.exists(), f"Log file not found: {log_path}"

    log_content = log_path.read_text(encoding="utf-8")

    assert "LIMIT" in log_content,   "Expected 'LIMIT' in log file."
    assert "BTCUSDT" in log_content, "Expected 'BTCUSDT' in log file."
    assert "150000" in log_content,  "Expected price '150000' in log file."

    print(f"✓ LIMIT order test passed. Log: {log_path}")


def test_limit_order_missing_price():
    """LIMIT order without --price must exit with code 1 (validation error)."""
    result = subprocess.run(
        [
            sys.executable, "cli.py",
            "--symbol", "BTCUSDT",
            "--side",   "BUY",
            "--type",   "LIMIT",
            "--qty",    "0.001",
            # --price intentionally omitted
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, (
        f"Expected exit code 1 for missing price, got {result.returncode}."
    )
    print("✓ Missing-price validation test passed.")
