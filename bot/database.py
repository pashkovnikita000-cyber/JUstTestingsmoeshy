from __future__ import annotations

import os

import aiosqlite

from bot import config


async def init_db() -> None:
    db_path = config.DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Migrate from per-user schema to shared schema if needed
        async with db.execute("PRAGMA table_info(wallets)") as cur:
            columns = {row[1] for row in await cur.fetchall()}
        if "user_id" in columns:
            await db.execute("DROP TABLE wallets")
            await db.execute("DROP TABLE IF EXISTS sent_alerts")
            await db.commit()

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS wallets (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                address    TEXT    NOT NULL UNIQUE,
                name       TEXT    NOT NULL,
                last_block INTEGER DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash    TEXT    NOT NULL UNIQUE,
                alerted_at TEXT    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def count_wallets() -> int:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM wallets") as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 0


async def wallet_exists(address: str) -> bool:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM wallets WHERE address = ? LIMIT 1", (address,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_wallet(address: str, name: str) -> bool:
    """Insert wallet; return False if address already tracked."""
    if await wallet_exists(address):
        return False
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO wallets (address, name) VALUES (?, ?)", (address, name)
        )
        await db.commit()
    return True


async def get_wallets() -> list[dict]:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, address FROM wallets ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"name": row["name"], "address": row["address"]} for row in rows]


async def remove_wallet(address: str) -> bool:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM wallets WHERE address = ?", (address,)
        )
        await db.commit()
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Monitoring CRUD (MON-01, DATA-02)
# ---------------------------------------------------------------------------

async def get_all_wallets() -> list[dict]:
    """Return all wallets for polling loop: {address, name, last_block}."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT address, name, last_block FROM wallets ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def update_last_block(address: str, block_number: int) -> None:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "UPDATE wallets SET last_block = ? WHERE address = ?",
            (block_number, address),
        )
        await db.commit()


async def is_alert_sent(tx_hash: str) -> bool:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM sent_alerts WHERE tx_hash = ? LIMIT 1", (tx_hash,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def mark_alert_sent(tx_hash: str) -> None:
    """INSERT OR IGNORE — idempotent."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO sent_alerts (tx_hash) VALUES (?)", (tx_hash,)
        )
        await db.commit()
