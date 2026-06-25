from __future__ import annotations

import os

import aiosqlite

from bot import config

# ponytail: single connection per call — no pool needed at < 100 wallets / single user


async def init_db() -> None:
    db_path = config.DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS wallets (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                address  TEXT    NOT NULL,
                name     TEXT    NOT NULL,
                last_block INTEGER DEFAULT 0,
                UNIQUE(user_id, address)
            )
            """
        )
        await db.commit()


async def count_wallets(user_id: int) -> int:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM wallets WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
