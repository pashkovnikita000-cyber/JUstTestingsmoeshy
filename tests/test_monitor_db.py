"""Tests for monitoring-related DB functions (MON-01, DATA-02)."""
from __future__ import annotations

import pytest
import pytest_asyncio

import bot.config
from bot.database import (
    add_wallet,
    init_db,
    get_all_wallets,
    update_last_block,
    is_alert_sent,
    mark_alert_sent,
)

ADDR_1 = "0x" + "a" * 40
ADDR_2 = "0x" + "b" * 40
TX_HASH = "0x" + "f" * 64


@pytest_asyncio.fixture
async def db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_monitor.db")
    monkeypatch.setattr(bot.config, "DATABASE_PATH", db_file)
    await init_db()
    yield db_file


class TestSentAlertsTable:
    async def test_sent_alerts_table_created(self, db):
        import aiosqlite
        async with aiosqlite.connect(db) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sent_alerts'"
            ) as cur:
                row = await cur.fetchone()
        assert row is not None


class TestGetAllWallets:
    async def test_empty_when_no_wallets(self, db):
        assert await get_all_wallets() == []

    async def test_returns_all_wallets(self, db):
        await add_wallet(ADDR_1, "A1")
        await add_wallet(ADDR_2, "B2")
        assert len(await get_all_wallets()) == 2

    async def test_returns_required_fields(self, db):
        await add_wallet(ADDR_1, "MyWallet")
        result = await get_all_wallets()
        row = result[0]
        assert row["address"] == ADDR_1
        assert row["name"] == "MyWallet"
        assert "last_block" in row

    async def test_initial_last_block_is_zero(self, db):
        await add_wallet(ADDR_1, "Test")
        assert (await get_all_wallets())[0]["last_block"] == 0


class TestUpdateLastBlock:
    async def test_updates_matching_wallet(self, db):
        await add_wallet(ADDR_1, "Test")
        await update_last_block(ADDR_1, 12345)
        assert (await get_all_wallets())[0]["last_block"] == 12345

    async def test_does_not_affect_other_address(self, db):
        await add_wallet(ADDR_1, "First")
        await add_wallet(ADDR_2, "Second")
        await update_last_block(ADDR_1, 5000)
        wallets = await get_all_wallets()
        addr1 = next(w for w in wallets if w["address"] == ADDR_1)
        addr2 = next(w for w in wallets if w["address"] == ADDR_2)
        assert addr1["last_block"] == 5000
        assert addr2["last_block"] == 0


class TestIsAlertSent:
    async def test_returns_false_when_not_sent(self, db):
        assert await is_alert_sent(TX_HASH) is False

    async def test_returns_true_after_mark(self, db):
        await mark_alert_sent(TX_HASH)
        assert await is_alert_sent(TX_HASH) is True


class TestMarkAlertSent:
    async def test_idempotent_double_call(self, db):
        await mark_alert_sent(TX_HASH)
        await mark_alert_sent(TX_HASH)  # must not raise
        assert await is_alert_sent(TX_HASH) is True

    async def test_different_hashes_independent(self, db):
        other_hash = "0x" + "e" * 64
        await mark_alert_sent(TX_HASH)
        assert await is_alert_sent(other_hash) is False
