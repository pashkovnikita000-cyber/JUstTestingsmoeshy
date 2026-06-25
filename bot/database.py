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
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash    TEXT    NOT NULL,
                user_id    INTEGER NOT NULL,
                alerted_at TEXT    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tx_hash, user_id)
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


async def wallet_exists(user_id: int, address: str) -> bool:
    """Return True iff (user_id, address) already in wallets. WALLET-05."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM wallets WHERE user_id = ? AND address = ? LIMIT 1",
            (user_id, address),
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_wallet(user_id: int, address: str, name: str) -> bool:
    """Insert wallet; return False if (user_id, address) already tracked (D-03)."""
    if await wallet_exists(user_id, address):
        return False
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO wallets (user_id, address, name) VALUES (?, ?, ?)",
            (user_id, address, name),
        )
        await db.commit()
    return True


async def get_wallets(user_id: int) -> list[dict]:
    """Return list of {name, address} dicts for user (WALLET-05: own only)."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, address FROM wallets WHERE user_id = ? ORDER BY id",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"name": row["name"], "address": row["address"]} for row in rows]


async def remove_wallet(user_id: int, address: str) -> bool:
    """Delete wallet by (user_id, address). Returns True if deleted (WALLET-05)."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM wallets WHERE user_id = ? AND address = ?",
            (user_id, address),
        )
        await db.commit()
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Monitoring CRUD (MON-01, DATA-02)
# ---------------------------------------------------------------------------

async def get_all_wallets() -> list[dict]:
    """Return all wallets across all users for polling loop: {user_id, address, name, last_block}."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, address, name, last_block FROM wallets ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def update_last_block(user_id: int, address: str, block_number: int) -> None:
    """Update last_block for (user_id, address) pair — compound key prevents cross-user updates (T-02-03)."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "UPDATE wallets SET last_block = ? WHERE user_id = ? AND address = ?",
            (block_number, user_id, address),
        )
        await db.commit()


async def is_alert_sent(tx_hash: str, user_id: int) -> bool:
    """Return True iff (tx_hash, user_id) already in sent_alerts."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM sent_alerts WHERE tx_hash = ? AND user_id = ? LIMIT 1",
            (tx_hash, user_id),
        ) as cursor:
            return await cursor.fetchone() is not None


async def mark_alert_sent(tx_hash: str, user_id: int) -> None:
    """Record (tx_hash, user_id) as alerted. INSERT OR IGNORE — idempotent (T-02-04)."""
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO sent_alerts (tx_hash, user_id) VALUES (?, ?)",
            (tx_hash, user_id),
        )
        await db.commit()
