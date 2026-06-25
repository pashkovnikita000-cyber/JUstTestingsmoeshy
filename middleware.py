from __future__ import annotations

from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bot import config


def restricted(handler: Callable) -> Callable:
    """Whitelist middleware — blocks any user not in ALLOWED_USER_IDS (AUTH-02)."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None or user.id not in config.ALLOWED_USER_IDS:
            if update.message:
                await update.message.reply_text("Access denied")
            return
        return await handler(update, context)

    return wrapper
