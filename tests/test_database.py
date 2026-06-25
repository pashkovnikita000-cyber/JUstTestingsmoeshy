"""Tests for bot/database.py — shared wallet CRUD."""
from __future__ import annotations

import pytest
import pytest_asyncio

import bot.config
from bot.database import (
    add_wallet,
    count_wallets,
    get_wallets,
    init_db,
    remove_wallet,
    wallet_exists,
)

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
        assert await add_wallet(ADDR_1, "Test") is True

    async def test_duplicate_returns_false(self, db):
        await add_wallet(ADDR_1, "First")
        assert await add_wallet(ADDR_1, "Second") is False

    async def test_duplicate_does_not_update_name(self, db):
        await add_wallet(ADDR_1, "First")
        await add_wallet(ADDR_1, "Second")
        wallets = await get_wallets()
        assert len(wallets) == 1
        assert wallets[0]["name"] == "First"

    async def test_two_different_addresses(self, db):
        assert await add_wallet(ADDR_1, "One") is True
        assert await add_wallet(ADDR_2, "Two") is True
        assert len(await get_wallets()) == 2


class TestWalletExists:
    async def test_returns_false_when_absent(self, db):
        assert await wallet_exists(ADDR_1) is False

    async def test_returns_true_after_add(self, db):
        await add_wallet(ADDR_1, "Test")
        assert await wallet_exists(ADDR_1) is True


class TestGetWallets:
    async def test_empty_list(self, db):
        assert await get_wallets() == []

    async def test_returns_all_wallets(self, db):
        await add_wallet(ADDR_1, "First")
        await add_wallet(ADDR_2, "Second")
        result = await get_wallets()
        assert len(result) == 2

    async def test_returns_name_and_address_fields(self, db):
        await add_wallet(ADDR_1, "MyWallet")
        result = await get_wallets()
        assert result[0]["name"] == "MyWallet"
        assert result[0]["address"] == ADDR_1


class TestCountWallets:
    async def test_zero_when_empty(self, db):
        assert await count_wallets() == 0

    async def test_counts_all(self, db):
        await add_wallet(ADDR_1, "One")
        await add_wallet(ADDR_2, "Two")
        assert await count_wallets() == 2


class TestRemoveWallet:
    async def test_remove_existing(self, db):
        await add_wallet(ADDR_1, "Test")
        assert await remove_wallet(ADDR_1) is True
        assert await wallet_exists(ADDR_1) is False

    async def test_remove_returns_false_not_found(self, db):
        assert await remove_wallet(ADDR_1) is False
