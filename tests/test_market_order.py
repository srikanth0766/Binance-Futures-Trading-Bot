"""
tests/test_market_order.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Integration test – MARKET order on Binance Futures Testnet.

Invokes ``cli.py`` as a subprocess to simulate real usage and verify:
  • The command exits with code 0.
  • A log file is created and contains expected keywords.
  • The output contains the order response fields.

Prerequisites:
  • Valid ``BINANCE_API_KEY`` and ``BINANCE_SECRET_KEY`` in ``.env``.
  • A network connection to https://testnet.binancefuture.com.

Run:
    cd trading_bot
    python -m pytest tests/test_market_order.py -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Project root (parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_market_buy_order():
    """Place a MARKET BUY and assert exit 0 + log written."""
    result = subprocess.run(
        [
            sys.executable, "cli.py",
            "--symbol", "BTCUSDT",
            "--side",   "BUY",
            "--type",   "MARKET",
            "--qty",    "0.01",
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

    # Log file must exist
    log_path = PROJECT_ROOT / "logs" / "trading_bot.log"
    assert log_path.exists(), f"Log file not found: {log_path}"

    log_content = log_path.read_text(encoding="utf-8")

    # Check that MARKET order was logged
    assert "MARKET" in log_content, "Expected 'MARKET' in log file."
    assert "BTCUSDT" in log_content, "Expected 'BTCUSDT' in log file."
    assert "orderId" in log_content or "order placed" in log_content.lower(), (
        "Expected order placement confirmation in log."
    )

    print(f"✓ MARKET order test passed. Log: {log_path}")
