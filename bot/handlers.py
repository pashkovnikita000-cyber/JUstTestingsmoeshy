from __future__ import annotations

import asyncio
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.database import add_wallet, count_wallets, get_wallets, remove_wallet, wallet_exists
from bot.etherscan import get_balance, get_eth_price, get_usdc_balance, validate_address
from bot.middleware import restricted

ASK_ADDRESS = 0
ASK_NAME = 1

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("➕ Добавить кошелёк"), KeyboardButton("👛 Кошельки")],
        [KeyboardButton("🗑 Удалить кошелёк")],
    ],
    resize_keyboard=True,
)


def shorten(address: str) -> str:
    return f"{address[:6]}...{address[-4:]}"


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    n = await count_wallets()
    await update.message.reply_text(
        f"✅ Bot is running. Tracking {n} wallets.",
        reply_markup=MAIN_KEYBOARD,
    )


@restricted
async def addwallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Send me the ETH wallet address:")
    return ASK_ADDRESS


async def addwallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    addr = update.message.text.strip()

    if not validate_address(addr):
        await update.message.reply_text(
            "Invalid ETH address. Must start with 0x followed by 40 hex characters.\n"
            "Please try again or /cancel."
        )
        return ASK_ADDRESS

    if await wallet_exists(addr):
        await update.message.reply_text("Wallet already tracked.")
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["pending_address"] = addr
    await update.message.reply_text("Got it! Now send a name for this wallet:")
    return ASK_NAME


async def addwallet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    addr = context.user_data.pop("pending_address", None)

    if not addr:
        await update.message.reply_text("Something went wrong. Please /addwallet again.")
        return ConversationHandler.END

    await add_wallet(addr, name)

    short = shorten(addr)
    try:
        balance: Decimal = await get_balance(addr)
        price: Decimal = await get_eth_price()
        await asyncio.sleep(0.25)
        usdc: Decimal = await get_usdc_balance(addr)
        usd = (balance * price).quantize(Decimal("0.01"))
        eth_str = f"{balance:.6f}".rstrip("0").rstrip(".")
        usdc_str = f"{usdc:,.2f}"
        await update.message.reply_text(
            f"✅ Added *{name}* `{short}`\n"
            f"ETH: {eth_str} (${usd:,})\n"
            f"USDC: ${usdc_str}",
            parse_mode="Markdown",
        )
    except Exception:
        await update.message.reply_text(
            f"✅ Added *{name}* `{short}`\n"
            "Balance: temporarily unavailable.",
            parse_mode="Markdown",
        )

    return ConversationHandler.END


@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END


@restricted
async def wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    wallet_list = await get_wallets()

    if not wallet_list:
        await update.message.reply_text("No wallets tracked. Use /addwallet", reply_markup=MAIN_KEYBOARD)
        return

    try:
        price: Decimal = await get_eth_price()
    except Exception:
        price = Decimal("0")

    lines: list[str] = []
    for w in wallet_list:
        short = shorten(w["address"])
        try:
            balance = await get_balance(w["address"])
            await asyncio.sleep(0.25)
            usdc = await get_usdc_balance(w["address"])
            usd = (balance * price).quantize(Decimal("0.01"))
            eth_str = f"{balance:.6f}".rstrip("0").rstrip(".")
            usd_str = f"${usd:,}" if price else "N/A"
            usdc_str = f"{usdc:,.2f}"
            lines.append(
                f"*{w['name']}* `{short}`\n"
                f"ETH: {eth_str} ({usd_str})\n"
                f"USDC: ${usdc_str}"
            )
        except Exception:
            lines.append(f"*{w['name']}* `{short}`\nBalance: temporarily unavailable")
        await asyncio.sleep(0.25)

    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


@restricted
async def removewallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        addr = context.args[0].strip()
        removed = await remove_wallet(addr)
        if removed:
            await update.message.reply_text(f"✅ Removed wallet {shorten(addr)}.", reply_markup=MAIN_KEYBOARD)
        else:
            await update.message.reply_text("Wallet not found.", reply_markup=MAIN_KEYBOARD)
        return

    wallet_list = await get_wallets()
    if not wallet_list:
        await update.message.reply_text("No wallets tracked.", reply_markup=MAIN_KEYBOARD)
        return

    buttons = [
        [InlineKeyboardButton(f"🗑 {w['name']} ({shorten(w['address'])})", callback_data=f"remove:{w['address']}")]
        for w in wallet_list
    ]
    await update.message.reply_text(
        "Выберите кошелёк для удаления:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    from bot import config as _cfg
    user = update.effective_user
    if user is None or user.id not in _cfg.ALLOWED_USER_IDS:
        await query.edit_message_text("Access denied")
        return

    addr = query.data.split(":", 1)[1]
    removed = await remove_wallet(addr)
    if removed:
        await query.edit_message_text(f"✅ Удалён кошелёк {shorten(addr)}.")
    else:
        await query.edit_message_text("Кошелёк не найден.")
