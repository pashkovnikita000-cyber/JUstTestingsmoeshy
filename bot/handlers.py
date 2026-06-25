from __future__ import annotations

import asyncio
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.database import add_wallet, count_wallets, get_wallets, remove_wallet, wallet_exists
from bot.etherscan import get_balance, get_eth_price, validate_address
from bot.middleware import restricted

# ---------------------------------------------------------------------------
# Conversation states for /addwallet dialog (D-01)
# ---------------------------------------------------------------------------

ASK_ADDRESS = 0
ASK_NAME = 1


def shorten(address: str) -> str:
    """Return 6+...+4 abbreviated address: 0xABCD...1234 (specifics)."""
    return f"{address[:6]}...{address[-4:]}"


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    n = await count_wallets(user.id)
    await update.message.reply_text(f"✅ Bot is running. Tracking {n} wallets.")


# ---------------------------------------------------------------------------
# /addwallet ConversationHandler (D-01, D-02, D-03)
# ---------------------------------------------------------------------------

@restricted
async def addwallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: prompt for ETH address."""
    await update.message.reply_text("Send me the ETH wallet address:")
    return ASK_ADDRESS


async def addwallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ASK_ADDRESS state: validate address (WALLET-02, T-01-10)."""
    addr = update.message.text.strip()

    if not validate_address(addr):
        await update.message.reply_text(
            "Invalid ETH address. Must start with 0x followed by 40 hex characters.\n"
            "Please try again or /cancel."
        )
        return ASK_ADDRESS  # stay in state, ask again

    user_id = update.effective_user.id
    if await wallet_exists(user_id, addr):
        await update.message.reply_text("Wallet already tracked.")
        context.user_data.clear()
        return ConversationHandler.END  # D-03

    context.user_data["pending_address"] = addr
    await update.message.reply_text("Got it! Now send a name for this wallet:")
    return ASK_NAME


async def addwallet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ASK_NAME state: save wallet and show initial balance (WALLET-01, specifics)."""
    name = update.message.text.strip()
    addr = context.user_data.pop("pending_address", None)
    user_id = update.effective_user.id

    if not addr:
        await update.message.reply_text("Something went wrong. Please /addwallet again.")
        return ConversationHandler.END

    await add_wallet(user_id, addr, name)

    short = shorten(addr)
    try:
        balance: Decimal = await get_balance(addr)
        price: Decimal = await get_eth_price()
        usd = (balance * price).quantize(Decimal("0.01"))
        eth_str = f"{balance:.6f}".rstrip("0").rstrip(".")
        await update.message.reply_text(
            f"✅ Added *{name}* `{short}`\n"
            f"Balance: {eth_str} ETH (${usd:,})",
            parse_mode="Markdown",
        )
    except Exception:  # T-01-13: degrade gracefully, wallet is saved
        await update.message.reply_text(
            f"✅ Added *{name}* `{short}`\n"
            "Balance: temporarily unavailable.",
            parse_mode="Markdown",
        )

    return ConversationHandler.END


@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """D-02: /cancel — abort dialog without saving."""
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# /wallets (WALLET-03, D-04, D-05, D-06)
# ---------------------------------------------------------------------------

@restricted
async def wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    wallet_list = await get_wallets(user_id)

    if not wallet_list:
        await update.message.reply_text("No wallets tracked. Use /addwallet")  # D-05
        return

    try:
        price: Decimal = await get_eth_price()
    except Exception:
        price = Decimal("0")  # T-01-13: show wallets even if price fetch fails

    lines: list[str] = []
    for w in wallet_list:
        short = shorten(w["address"])
        try:
            balance = await get_balance(w["address"])
            usd = (balance * price).quantize(Decimal("0.01"))
            eth_str = f"{balance:.6f}".rstrip("0").rstrip(".")
            usd_str = f"${usd:,}" if price else "N/A"
            lines.append(f"*{w['name']}* `{short}`\nBalance: {eth_str} ETH ({usd_str})")
        except Exception:  # T-01-13
            lines.append(f"*{w['name']}* `{short}`\nBalance: temporarily unavailable")
        await asyncio.sleep(0.25)  # D-06: throttle — no asyncio.gather (T-01-12)

    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# /removewallet (WALLET-04, WALLET-05)
# ---------------------------------------------------------------------------

@restricted
async def removewallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /removewallet <address>")
        return

    addr = context.args[0].strip()
    user_id = update.effective_user.id
    removed = await remove_wallet(user_id, addr)

    if removed:
        await update.message.reply_text(f"Removed wallet {shorten(addr)}.")
    else:
        await update.message.reply_text("Wallet not found.")
