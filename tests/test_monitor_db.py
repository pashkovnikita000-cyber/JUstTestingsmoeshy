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

USER_A = 111
USER_B = 222
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
    async def test_sent_alerts_table_created(self, db, monkeypatch):
        """init_db() creates sent_alerts table (DATA-02)."""
        import aiosqlite
        async with aiosqlite.connect(db) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sent_alerts'"
            ) as cur:
                row = await cur.fetchone()
        assert row is not None


class TestGetAllWallets:
    async def test_empty_when_no_wallets(self, db):
        result = await get_all_wallets()
        assert result == []

    async def test_returns_all_wallets_across_users(self, db):
        await add_wallet(USER_A, ADDR_1, "A1")
        await add_wallet(USER_B, ADDR_2, "B2")
        result = await get_all_wallets()
        assert len(result) == 2

    async def test_returns_required_fields(self, db):
        await add_wallet(USER_A, ADDR_1, "MyWallet")
        result = await get_all_wallets()
        assert len(result) == 1
        row = result[0]
        assert row["user_id"] == USER_A
        assert row["address"] == ADDR_1
        assert row["name"] == "MyWallet"
        assert "last_block" in row

    async def test_initial_last_block_is_zero(self, db):
        await add_wallet(USER_A, ADDR_1, "Test")
        result = await get_all_wallets()
        assert result[0]["last_block"] == 0


class TestUpdateLastBlock:
    async def test_updates_matching_wallet(self, db):
        await add_wallet(USER_A, ADDR_1, "Test")
        await update_last_block(USER_A, ADDR_1, 12345)
        wallets = await get_all_wallets()
        assert wallets[0]["last_block"] == 12345

    async def test_does_not_affect_other_user_same_address(self, db):
        await add_wallet(USER_A, ADDR_1, "A's wallet")
        await add_wallet(USER_B, ADDR_1, "B's wallet")
        await update_last_block(USER_A, ADDR_1, 99999)
        wallets = await get_all_wallets()
        wallet_a = next(w for w in wallets if w["user_id"] == USER_A)
        wallet_b = next(w for w in wallets if w["user_id"] == USER_B)
        assert wallet_a["last_block"] == 99999
        assert wallet_b["last_block"] == 0  # untouched

    async def test_does_not_affect_different_address_same_user(self, db):
        await add_wallet(USER_A, ADDR_1, "First")
        await add_wallet(USER_A, ADDR_2, "Second")
        await update_last_block(USER_A, ADDR_1, 5000)
        wallets = await get_all_wallets()
        addr1_wallet = next(w for w in wallets if w["address"] == ADDR_1)
        addr2_wallet = next(w for w in wallets if w["address"] == ADDR_2)
        assert addr1_wallet["last_block"] == 5000
        assert addr2_wallet["last_block"] == 0


class TestIsAlertSent:
    async def test_returns_false_when_not_sent(self, db):
        result = await is_alert_sent(TX_HASH, USER_A)
        assert result is False

    async def test_returns_true_after_mark(self, db):
        await mark_alert_sent(TX_HASH, USER_A)
        result = await is_alert_sent(TX_HASH, USER_A)
        assert result is True


class TestMarkAlertSent:
    async def test_idempotent_double_call(self, db):
        """INSERT OR IGNORE — no exception on duplicate (DATA-02)."""
        await mark_alert_sent(TX_HASH, USER_A)
        await mark_alert_sent(TX_HASH, USER_A)  # must not raise
        assert await is_alert_sent(TX_HASH, USER_A) is True

    async def test_user_isolation(self, db):
        """(hash, user_A) and (hash, user_B) are independent rows."""
        await mark_alert_sent(TX_HASH, USER_A)
        assert await is_alert_sent(TX_HASH, USER_A) is True
        assert await is_alert_sent(TX_HASH, USER_B) is False
