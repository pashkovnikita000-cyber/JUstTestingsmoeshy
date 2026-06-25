"""Etherscan API client — validate addresses, fetch balance and ETH price."""
from __future__ import annotations

import asyncio
import re
import time
from decimal import Decimal

import aiohttp

from bot import config

_BASE_URL = "https://api.etherscan.io/v2/api"
_CHAIN_ID = "1"  # Ethereum mainnet
_USDC_CONTRACT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
_USDC_DECIMALS = 6
_MIN_INTERVAL = 0.25  # seconds between requests (D-06, D-12: free tier 5 req/sec)

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Module-level throttle state.
# ponytail: global lock, per-wallet locks if concurrent fetch ever needed
_last_request: float = 0.0


# ---------------------------------------------------------------------------
# Pure helpers (no I/O — unit-testable without network)
# ---------------------------------------------------------------------------

def validate_address(addr: str) -> bool:
    """Return True iff addr is a valid ETH address (0x + 40 hex chars). WALLET-02."""
    if not isinstance(addr, str) or not addr.strip():
        return False
    return bool(ADDRESS_RE.match(addr))


def wei_to_eth(wei: int | str) -> Decimal:
    """Convert wei amount (int or str) to ETH as Decimal. No float arithmetic."""
    return Decimal(str(wei)) / Decimal(10 ** 18)


def _parse_transactions(payload: dict) -> list[dict]:
    """Parse Etherscan txlist response. Returns [] for 'No transactions found'. T-02-04."""
    if str(payload.get("status")) != "1":
        result = payload.get("result", "")
        if isinstance(result, str) and "No transactions found" in result:
            return []
        msg = payload.get("message") or result or "unknown error"
        raise ValueError(f"Etherscan txlist error: {msg}")
    result = payload.get("result")
    if not isinstance(result, list):
        return []
    return [
        {
            "hash": tx["hash"],
            "from_addr": tx["from"],  # avoids Python reserved word
            "to_addr": tx["to"],
            "value_wei": tx["value"],  # str — Decimal conversion at alert time
            "block_number": int(tx["blockNumber"]),
            "is_error": tx["isError"] != "0",
        }
        for tx in result
    ]


def _parse_current_block(payload: dict) -> int:
    """Parse eth_blockNumber hex response to int. T-02-02."""
    try:
        return int(payload["result"], 16)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Etherscan block number parse error: {exc}") from exc


def _parse_balance(payload: dict) -> Decimal:
    """Extract ETH balance from Etherscan account/balance response. T-01-06."""
    if str(payload.get("status")) != "1":
        msg = payload.get("message") or payload.get("result") or "unknown error"
        raise ValueError(f"Etherscan balance error: {msg}")
    return wei_to_eth(payload["result"])


def _parse_price(payload: dict) -> Decimal:
    """Extract ETH/USD price from Etherscan stats/ethprice response. T-01-06."""
    try:
        return Decimal(payload["result"]["ethusd"])
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Etherscan price parse error: {exc}") from exc


# ---------------------------------------------------------------------------
# Async I/O (not covered by unit tests — only parsers above are)
# ---------------------------------------------------------------------------

async def _throttle() -> None:
    """Ensure >=0.25 s between consecutive Etherscan requests (D-06)."""
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < _MIN_INTERVAL:
        await asyncio.sleep(_MIN_INTERVAL - elapsed)
    _last_request = time.monotonic()


async def _get(params: dict, session: aiohttp.ClientSession | None = None) -> dict:
    """GET _BASE_URL with params, respecting throttle. Returns parsed JSON."""
    await _throttle()
    params = {**params, "chainid": _CHAIN_ID, "apikey": config.ETHERSCAN_API_KEY}
    own_session = session is None
    if own_session:
        session = aiohttp.ClientSession()
    try:
        async with session.get(_BASE_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()
    finally:
        if own_session:
            await session.close()


async def get_balance(address: str, session: aiohttp.ClientSession | None = None) -> Decimal:
    """Return wallet balance in ETH. Validates address before calling API (T-01-04)."""
    if not validate_address(address):
        raise ValueError(f"Invalid ETH address: {address!r}")
    payload = await _get(
        {"module": "account", "action": "balance", "address": address, "tag": "latest"},
        session=session,
    )
    return _parse_balance(payload)


async def get_eth_price(session: aiohttp.ClientSession | None = None) -> Decimal:
    """Return current ETH/USD price as Decimal."""
    payload = await _get({"module": "stats", "action": "ethprice"}, session=session)
    return _parse_price(payload)


async def get_transactions(address: str, start_block: int, session: aiohttp.ClientSession | None = None) -> list[dict]:
    """Fetch txlist for address starting at start_block. Returns [] if no new txs."""
    if not validate_address(address):
        raise ValueError(f"Invalid ETH address: {address!r}")
    payload = await _get(
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": str(start_block),
            "endblock": "99999999",
            "sort": "asc",
        },
        session=session,
    )
    return _parse_transactions(payload)


async def get_current_block(session: aiohttp.ClientSession | None = None) -> int:
    """Return current Ethereum block number (for last_block initialization)."""
    payload = await _get({"module": "proxy", "action": "eth_blockNumber"}, session=session)
    return _parse_current_block(payload)


async def get_usdc_balance(address: str, session: aiohttp.ClientSession | None = None) -> Decimal:
    """Return USDC token balance for address (mainnet ERC-20)."""
    if not validate_address(address):
        raise ValueError(f"Invalid ETH address: {address!r}")
    payload = await _get(
        {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": _USDC_CONTRACT,
            "address": address,
            "tag": "latest",
        },
        session=session,
    )
    if str(payload.get("status")) != "1":
        msg = payload.get("message") or payload.get("result") or "unknown error"
        raise ValueError(f"Etherscan USDC error: {msg}")
    return Decimal(str(payload["result"])) / Decimal(10 ** _USDC_DECIMALS)
