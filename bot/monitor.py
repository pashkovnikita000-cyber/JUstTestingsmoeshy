"""Background polling loop — checks wallets for new transactions every 60s (MON-01)."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

import aiohttp
from telegram.ext import Application

from bot.database import get_all_wallets, is_alert_sent, mark_alert_sent, update_last_block
from bot.etherscan import get_current_block, get_eth_price, get_transactions, wei_to_eth

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure helpers — unit-testable, no I/O (MON-02, MON-03)
# ---------------------------------------------------------------------------

def _should_alert(
    value_wei: str | int,
    eth_price: Decimal,
    threshold: Decimal = Decimal("100"),
) -> bool:
    """Return True iff tx value exceeds threshold USD (strictly greater-than)."""
    eth_amount = wei_to_eth(value_wei)
    usd_value = eth_amount * eth_price
    return usd_value > threshold


def _format_alert(
    wallet_name: str,
    wallet_address: str,
    tx: dict,
    eth_price: Decimal,
) -> str:
    """Format a Telegram Markdown alert message for a transaction (MON-03)."""
    is_incoming = tx["to_addr"].lower() == wallet_address.lower()
    direction = "📥 Входящая" if is_incoming else "📤 Исходящая"
    eth_amount = wei_to_eth(tx["value_wei"])
    usd_amount = eth_amount * eth_price
    tx_hash = tx["hash"]
    return (
        f"*{wallet_name}*\n\n"
        f"{direction}: `{eth_amount:.4f}` ETH (${usd_amount:,.2f})\n\n"
        f"Tx: `{tx_hash}`\n"
        f"https://etherscan.io/tx/{tx_hash}"
    )


async def _check_wallet(
    app: Application,  # type: ignore[type-arg]
    wallet: dict,
    eth_price: Decimal,
    session: aiohttp.ClientSession,
) -> None:
    address = wallet["address"]
    last_block = wallet["last_block"]

    if last_block == 0:
        # First run: initialize to current block, skip historical txns
        current_block = await get_current_block(session=session)
        await update_last_block(wallet["user_id"], address, current_block)
        logger.info("Initialized %s... at block %d", address[:10], current_block)
        return

    txns = await get_transactions(address, last_block + 1, session=session)
    if not txns:
        return

    max_block = max(tx["block_number"] for tx in txns)
    await update_last_block(wallet["user_id"], address, max_block)
    # ponytail: alert dispatch added in 02-02 — intentional stub here


async def _check_wallets(app: Application) -> None:  # type: ignore[type-arg]
    wallets = await get_all_wallets()
    if not wallets:
        return

    async with aiohttp.ClientSession() as session:
        try:
            eth_price = await get_eth_price(session=session)
        except Exception:
            logger.warning("Failed to fetch ETH price; using 0 as fallback")
            eth_price = Decimal("0")

        for wallet in wallets:
            try:
                await _check_wallet(app, wallet, eth_price, session)
            except Exception:
                logger.exception("Error checking wallet %s", wallet.get("address", "?"))


async def _monitor_loop(app: Application) -> None:  # type: ignore[type-arg]
    await asyncio.sleep(10)  # startup delay
    while True:
        try:
            await _check_wallets(app)
        except asyncio.CancelledError:
            raise  # propagate cleanly for shutdown (T-02-01)
        except Exception:
            logger.exception("Monitor cycle failed")
        await asyncio.sleep(60)


def start_polling(app: Application) -> None:  # type: ignore[type-arg]
    """Schedule the monitor loop as an asyncio task. Call from post_init (async context)."""
    asyncio.create_task(_monitor_loop(app))
    logger.info("Monitor polling started (60s interval)")
