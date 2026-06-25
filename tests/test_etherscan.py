"""Tests for bot/etherscan.py — pure functions only (no network)."""
from decimal import Decimal

import pytest

from bot.etherscan import _parse_balance, _parse_price, validate_address, wei_to_eth


# ---------------------------------------------------------------------------
# validate_address
# ---------------------------------------------------------------------------

class TestValidateAddress:
    def test_valid_lowercase(self):
        assert validate_address("0x" + "a" * 40) is True

    def test_valid_uppercase(self):
        assert validate_address("0x" + "A" * 40) is True

    def test_valid_mixed_case(self):
        assert validate_address("0xAbCdEf" + "1234567890" * 3 + "abcd") is True

    def test_valid_all_digits(self):
        assert validate_address("0x" + "1" * 40) is True

    def test_empty_string(self):
        assert validate_address("") is False

    def test_too_short(self):
        assert validate_address("0x123") is False

    def test_too_long(self):
        assert validate_address("0x" + "a" * 41) is False

    def test_no_0x_prefix(self):
        assert validate_address("a" * 40) is False

    def test_invalid_hex_chars(self):
        assert validate_address("0x" + "Z" * 40) is False

    def test_only_0x(self):
        assert validate_address("0x") is False

    def test_none_like_empty(self):
        # Python caller contract: must pass str; empty string is falsy case
        assert validate_address("   ") is False


# ---------------------------------------------------------------------------
# wei_to_eth
# ---------------------------------------------------------------------------

class TestWeiToEth:
    def test_one_eth(self):
        result = wei_to_eth(10 ** 18)
        assert result == Decimal("1")
        assert isinstance(result, Decimal)

    def test_half_eth_from_int(self):
        result = wei_to_eth(5 * 10 ** 17)
        assert result == Decimal("0.5")

    def test_half_eth_from_string(self):
        result = wei_to_eth("500000000000000000")
        assert result == Decimal("0.5")

    def test_zero(self):
        assert wei_to_eth(0) == Decimal("0")

    def test_small_amount(self):
        # 1 wei == 1e-18 ETH
        result = wei_to_eth(1)
        assert result == Decimal("1") / Decimal(10 ** 18)

    def test_returns_decimal_not_float(self):
        result = wei_to_eth(10 ** 18)
        assert type(result) is Decimal


# ---------------------------------------------------------------------------
# _parse_balance
# ---------------------------------------------------------------------------

class TestParseBalance:
    def test_one_eth(self):
        payload = {"status": "1", "message": "OK", "result": "1000000000000000000"}
        assert _parse_balance(payload) == Decimal("1")

    def test_half_eth(self):
        payload = {"status": "1", "message": "OK", "result": "500000000000000000"}
        assert _parse_balance(payload) == Decimal("0.5")

    def test_zero_balance(self):
        payload = {"status": "1", "message": "OK", "result": "0"}
        assert _parse_balance(payload) == Decimal("0")

    def test_error_status_raises(self):
        payload = {"status": "0", "message": "NOTOK", "result": "Error"}
        with pytest.raises(ValueError):
            _parse_balance(payload)

    def test_missing_result_raises(self):
        payload = {"status": "1", "message": "OK"}
        with pytest.raises((KeyError, ValueError)):
            _parse_balance(payload)


# ---------------------------------------------------------------------------
# _parse_price
# ---------------------------------------------------------------------------

class TestParsePrice:
    def test_typical_price(self):
        payload = {"result": {"ethusd": "3456.78", "ethbtc": "0.05"}}
        result = _parse_price(payload)
        assert result == Decimal("3456.78")
        assert isinstance(result, Decimal)

    def test_whole_number_price(self):
        payload = {"result": {"ethusd": "2000.00"}}
        assert _parse_price(payload) == Decimal("2000.00")

    def test_missing_result_raises(self):
        with pytest.raises((KeyError, ValueError)):
            _parse_price({})

    def test_missing_ethusd_raises(self):
        with pytest.raises((KeyError, ValueError)):
            _parse_price({"result": {}})

    def test_returns_decimal_not_float(self):
        payload = {"result": {"ethusd": "1234.56"}}
        assert type(_parse_price(payload)) is Decimal
