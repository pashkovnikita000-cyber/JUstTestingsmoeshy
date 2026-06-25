from __future__ import annotations

from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

from bot import config
from bot.database import init_db
from bot.handlers import (
    ASK_ADDRESS,
    ASK_NAME,
    addwallet_address,
    addwallet_name,
    addwallet_start,
    cancel,
    removewallet,
    start,
    wallets,
)


async def _post_init(app: Application) -> None:  # type: ignore[type-arg]
    await init_db()


def main() -> None:
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # /addwallet multi-step dialog (D-01) + /cancel fallback (D-02)
    addwallet_conv = ConversationHandler(
        entry_points=[CommandHandler("addwallet", addwallet_start)],
        states={
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, addwallet_address)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, addwallet_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(addwallet_conv)
    app.add_handler(CommandHandler("wallets", wallets))
    app.add_handler(CommandHandler("removewallet", removewallet))

    app.run_polling()


if __name__ == "__main__":
    main()
