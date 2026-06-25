from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.database import count_wallets
from bot.middleware import restricted


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    n = await count_wallets(user.id)
    await update.message.reply_text(f"✅ Bot is running. Tracking {n} wallets.")
