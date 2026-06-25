from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/wallets.db")


def _parse_user_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    return {int(uid.strip()) for uid in raw.split(",") if uid.strip()}


ALLOWED_USER_IDS: set[int] = _parse_user_ids(os.getenv("ALLOWED_USER_IDS"))
