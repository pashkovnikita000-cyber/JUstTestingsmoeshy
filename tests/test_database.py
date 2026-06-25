"""Tests for bot/database.py — CRUD with user_id isolation (WALLET-01, WALLET-03..05)."""
from __future__ import annotations

import pytest
import pytest_asyncio

import bot.config
from bot.database import (
    add_wallet,
    get_wallets,
    init_db,
    remove_wallet,
    wallet_exists,
)

USER_A = 111
USER_B = 222
ADDR_1 = "0x" + "a" * 40
ADDR_2 = "0x" + "b" * 40


@pytest_asyncio.fixture
async def db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(bot.config, "DATABASE_PATH", db_file)
    await init_db()
    yield db_file


class TestAddWallet:
    async def test_add_returns_true(self, db):
        result = await add_wallet(USER_A, ADDR_1, "Test")
        assert result is True

    async def test_duplicate_returns_false(self, db):
        await add_wallet(USER_A, ADDR_1, "First")
        result = await add_wallet(USER_A, ADDR_1, "Second")
        assert result is False

    async def test_duplicate_does_not_update_name(self, db):
        await add_wallet(USER_A, ADDR_1, "First")
        await add_wallet(USER_A, ADDR_1, "Second")
        wallets = await get_wallets(USER_A)
        assert len(wallets) == 1
        assert wallets[0]["name"] == "First"  # D-03: unchanged

    async def test_same_address_different_users_allowed(self, db):
        result_a = await add_wallet(USER_A, ADDR_1, "A wallet")
        result_b = await add_wallet(USER_B, ADDR_1, "B wallet")
        assert result_a is True
        assert result_b is True


class TestWalletExists:
    async def test_returns_false_when_absent(self, db):
        assert await wallet_exists(USER_A, ADDR_1) is False

    async def test_returns_true_after_add(self, db):
        await add_wallet(USER_A, ADDR_1, "Test")
        assert await wallet_exists(USER_A, ADDR_1) is True

    async def test_user_isolation(self, db):
        await add_wallet(USER_A, ADDR_1, "A's")
        # same address, different user — must not exist
        assert await wallet_exists(USER_B, ADDR_1) is False


class TestGetWallets:
    async def test_empty_list(self, db):
        assert await get_wallets(USER_A) == []

    async def test_returns_own_wallets_only(self, db):
        await add_wallet(USER_A, ADDR_1, "First")
        await add_wallet(USER_A, ADDR_2, "Second")
        result = await get_wallets(USER_A)
        assert len(result) == 2

    async def test_user_isolation(self, db):
        await add_wallet(USER_A, ADDR_1, "A wallet")
        await add_wallet(USER_B, ADDR_2, "B wallet")
        result_a = await get_wallets(USER_A)
        result_b = await get_wallets(USER_B)
        assert len(result_a) == 1
        assert result_a[0]["address"] == ADDR_1
        assert len(result_b) == 1
        assert result_b[0]["address"] == ADDR_2

    async def test_returns_name_and_address_fields(self, db):
        await add_wallet(USER_A, ADDR_1, "MyWallet")
        result = await get_wallets(USER_A)
        assert result[0]["name"] == "MyWallet"
        assert result[0]["address"] == ADDR_1


class TestRemoveWallet:
    async def test_remove_own_wallet(self, db):
        await add_wallet(USER_A, ADDR_1, "Test")
        result = await remove_wallet(USER_A, ADDR_1)
        assert result is True
        assert await wallet_exists(USER_A, ADDR_1) is False

    async def test_remove_returns_false_not_found(self, db):
        result = await remove_wallet(USER_A, ADDR_1)
        assert result is False

    async def test_cannot_remove_other_users_wallet(self, db):
        await add_wallet(USER_A, ADDR_1, "A's wallet")
        # USER_B tries to remove USER_A's wallet — WALLET-05
        result = await remove_wallet(USER_B, ADDR_1)
        assert result is False
        assert await wallet_exists(USER_A, ADDR_1) is True
