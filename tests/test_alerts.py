"""Tests for _should_alert and _format_alert pure functions (MON-02, MON-03)."""
from decimal import Decimal

import pytest

from bot.monitor import _format_alert, _should_alert

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

WALLET_ADDR = "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"
OTHER_ADDR  = "0x1111111111111111111111111111111111111111"

def _tx(*, value_wei="100000000000000000", to_addr=WALLET_ADDR, from_addr=OTHER_ADDR, is_error=False):
    return {
        "hash": "0xdeadbeef" + "0" * 56,
        "from_addr": from_addr,
        "to_addr": to_addr,
        "value_wei": value_wei,
        "block_number": 12345678,
        "is_error": is_error,
    }


# ---------------------------------------------------------------------------
# _should_alert
# ---------------------------------------------------------------------------

def test_should_alert_above_threshold():
    # 0.1 ETH * $2000 = $200 > $100
    assert _should_alert("100000000000000000", Decimal("2000")) is True


def test_should_alert_below_threshold():
    # 0.049 ETH * $2000 = $98 < $100
    assert _should_alert("49000000000000000", Decimal("2000")) is False


def test_should_alert_exactly_threshold_is_false():
    # 0.05 ETH * $2000 = $100 — strictly greater-than, NOT equal
    assert _should_alert("50000000000000000", Decimal("2000")) is False


def test_should_alert_zero_price_returns_false():
    # Safe fallback — no crash, no spurious alert
    assert _should_alert("100000000000000000", Decimal("0")) is False


def test_should_alert_accepts_int_value_wei():
    assert _should_alert(100000000000000000, Decimal("2000")) is True


def test_should_alert_accepts_str_value_wei():
    assert _should_alert("100000000000000000", Decimal("2000")) is True


# ---------------------------------------------------------------------------
# _format_alert — direction detection
# ---------------------------------------------------------------------------

def test_format_alert_incoming_direction():
    tx = _tx(to_addr=WALLET_ADDR, from_addr=OTHER_ADDR)
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "📥" in msg or "Incoming" in msg or "Входящая" in msg


def test_format_alert_outgoing_direction():
    tx = _tx(from_addr=WALLET_ADDR, to_addr=OTHER_ADDR)
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "📤" in msg or "Outgoing" in msg or "Исходящая" in msg


def test_format_alert_direction_case_insensitive():
    # wallet_address in lowercase, tx has mixed-case to_addr
    tx = _tx(to_addr=WALLET_ADDR.upper(), from_addr=OTHER_ADDR)
    msg = _format_alert("MyWallet", WALLET_ADDR.lower(), tx, Decimal("2000"))
    assert "📥" in msg or "Incoming" in msg or "Входящая" in msg


# ---------------------------------------------------------------------------
# _format_alert — content requirements
# ---------------------------------------------------------------------------

def test_format_alert_contains_wallet_name():
    tx = _tx()
    msg = _format_alert("CoolWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "CoolWallet" in msg


def test_format_alert_contains_tx_hash():
    tx = _tx()
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert tx["hash"] in msg


def test_format_alert_contains_etherscan_link():
    tx = _tx()
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "etherscan.io/tx/" in msg


def test_format_alert_eth_four_decimal_places():
    # 0.1 ETH → "0.1000"
    tx = _tx(value_wei="100000000000000000")
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "0.1000" in msg


def test_format_alert_usd_two_decimal_places():
    # 0.1 ETH * $2000 = $200.00
    tx = _tx(value_wei="100000000000000000")
    msg = _format_alert("MyWallet", WALLET_ADDR, tx, Decimal("2000"))
    assert "200.00" in msg
