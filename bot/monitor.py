"""Background polling loop — checks wallets for new transactions every 60s (MON-01)."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

import aiohttp
from telegram.ext import Application

from bot.database import get_all_wallets, update_last_block
from bot.etherscan import get_current_block, get_eth_price, get_transactions

logger = logging.getLogger(__name__)


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
