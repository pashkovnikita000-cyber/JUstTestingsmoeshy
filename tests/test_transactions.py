"""Tests for Etherscan txlist + eth_blockNumber pure parsers (MON-01, INFRA-03)."""
from __future__ import annotations

import pytest

from bot.etherscan import _parse_transactions, _parse_current_block


# ---------------------------------------------------------------------------
# Fixtures: realistic Etherscan API payloads
# ---------------------------------------------------------------------------

NO_TXS_PAYLOAD = {
    "status": "0",
    "message": "No transactions found",
    "result": "No transactions found",
}

ERROR_PAYLOAD = {
    "status": "0",
    "message": "NOTOK",
    "result": "Max rate limit reached",
}

EMPTY_LIST_PAYLOAD = {
    "status": "1",
    "message": "OK",
    "result": [],
}

TX_LIST_PAYLOAD = {
    "status": "1",
    "message": "OK",
    "result": [
        {
            "hash": "0xabc123",
            "from": "0x" + "1" * 40,
            "to": "0x" + "2" * 40,
            "value": "1000000000000000000",
            "blockNumber": "19000000",
            "timeStamp": "1700000000",
            "isError": "0",
        },
        {
            "hash": "0xdef456",
            "from": "0x" + "3" * 40,
            "to": "0x" + "4" * 40,
            "value": "500000000000000000",
            "blockNumber": "19000001",
            "timeStamp": "1700000060",
            "isError": "1",
        },
    ],
}

BLOCK_PAYLOAD = {"jsonrpc": "2.0", "id": 1, "result": "0xC4AF0B"}


# ---------------------------------------------------------------------------
# _parse_transactions
# ---------------------------------------------------------------------------

class TestParseTransactions:
    def test_no_txs_returns_empty_list(self):
        result = _parse_transactions(NO_TXS_PAYLOAD)
        assert result == []

    def test_error_payload_raises(self):
        with pytest.raises(ValueError):
            _parse_transactions(ERROR_PAYLOAD)

    def test_empty_list_result_returns_empty_list(self):
        result = _parse_transactions(EMPTY_LIST_PAYLOAD)
        assert result == []

    def test_returns_list_of_dicts(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert len(result) == 2

    def test_hash_key_present(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[0]["hash"] == "0xabc123"

    def test_from_addr_key_avoids_keyword(self):
        """from → from_addr to avoid Python reserved word collision."""
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert "from_addr" in result[0]
        assert "from" not in result[0]

    def test_to_addr_key(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert "to_addr" in result[0]

    def test_value_wei_kept_as_str(self):
        """value_wei stays as str — Decimal conversion happens at alert time."""
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[0]["value_wei"] == "1000000000000000000"
        assert isinstance(result[0]["value_wei"], str)

    def test_block_number_converted_to_int(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[0]["block_number"] == 19000000
        assert isinstance(result[0]["block_number"], int)

    def test_is_error_false_for_zero(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[0]["is_error"] is False

    def test_is_error_true_for_one(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[1]["is_error"] is True

    def test_second_tx_block_number(self):
        result = _parse_transactions(TX_LIST_PAYLOAD)
        assert result[1]["block_number"] == 19000001


# ---------------------------------------------------------------------------
# _parse_current_block
# ---------------------------------------------------------------------------

class TestParseCurrentBlock:
    def test_parses_hex_to_int(self):
        result = _parse_current_block(BLOCK_PAYLOAD)
        assert result == int("0xC4AF0B", 16)
        assert isinstance(result, int)

    def test_known_hex_value(self):
        payload = {"result": "0x1312D00"}
        assert _parse_current_block(payload) == 20000000

    def test_missing_result_raises(self):
        with pytest.raises(ValueError):
            _parse_current_block({})

    def test_malformed_hex_raises(self):
        with pytest.raises(ValueError):
            _parse_current_block({"result": "not_a_hex"})

    def test_none_result_raises(self):
        with pytest.raises(ValueError):
            _parse_current_block({"result": None})
