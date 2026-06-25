from __future__ import annotations

from telegram.ext import Application, CommandHandler

from bot import config
from bot.database import init_db
from bot.handlers import start


async def _post_init(app: Application) -> None:  # type: ignore[type-arg]
    await init_db()


def main() -> None:
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == "__main__":
    main()
