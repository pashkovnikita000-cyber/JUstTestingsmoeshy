# Walking Skeleton — Crypto Watcher Bot

**Phase:** 1
**Generated:** 2026-06-25

## Capability Proven End-to-End

Доверенный пользователь (из whitelist) отправляет `/start` в Telegram, бот читает SQLite и отвечает `✅ Bot is running. Tracking N wallets.` — это прогоняет полный стек Telegram long-poll → Python (python-telegram-bot v21 async) → whitelist middleware → aiosqlite read → ответ. Пользователь не из whitelist получает `Access denied`.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | python-telegram-bot 21.x (async, long-polling) | Long-poll не требует домена/SSL — деплой на Railway проще (D-10). Async совместим с aiosqlite/aiohttp. |
| Data layer | SQLite через aiosqlite | Нет multi-write нагрузки, < 100 кошельков для личного бота (D-09). На Railway требует persistent volume. |
| Config | `.env` + python-dotenv, парсинг в `bot/config.py` | Один источник секретов: BOT_TOKEN, ETHERSCAN_API_KEY, ALLOWED_USER_IDS, DATABASE_PATH (INFRA-02). |
| Auth | Whitelist в `.env` (ALLOWED_USER_IDS), не в БД | Простота важнее гибкости (D-11). Применяется как middleware ко всем хендлерам (AUTH-01, AUTH-02). |
| External data | Etherscan free tier (aiohttp) | Бесплатно, не нужен full node (D-12). Throttle 0.25 сек между запросами (D-06). |
| Directory layout | Плоский пакет `bot/` (config, database, etherscan, handlers, middleware, main) | Задан в CLAUDE.md. Phase 2 добавит `monitor.py` без изменения структуры. |
| Entry / local run | `python -m bot.main` | Загружает `.env`, вызывает `init_db()`, стартует polling. |

## Stack Touched in Phase 1

- [x] Project scaffold — `bot/` пакет, `requirements.txt`, `.env.example`, `pytest`
- [x] Routing — Telegram CommandHandler `/start` (+ ConversationHandler для `/addwallet` в 01-03)
- [x] Database — real read (`count_wallets` в `/start`) AND real write (`add_wallet` в 01-03)
- [x] UI — интерактивная команда бота, отвечающая реальными данными
- [x] Deployment — задокументированная команда локального запуска `python -m bot.main` (Docker/Railway — Phase 2)

## Out of Scope (Deferred to Later Slices)

- Фоновый polling транзакций (`monitor.py`) — Phase 2 (MON-01..04)
- Таблица `sent_alerts` и дедупликация — Phase 2 (D-08, DATA-02 last_block уже в схеме per D-07, но не используется в Phase 1)
- Dockerfile, Railway config, README деплоя — Phase 2 (INFRA-01)
- Rate limiting Etherscan с буфером 4 req/sec — Phase 2 (INFRA-03); в Phase 1 только простой throttle 0.25 сек
- Настраиваемый порог, другие EVM сети, inline-кнопки — v2

## Subsequent Slice Plan

- **01-01** (этот скелет): whitelist + `/start` + SQLite schema (wallets + last_block per D-07)
- **01-02**: Etherscan client — валидация адреса, getBalance, ETH/USD price (питание для балансов)
- **01-03**: Wallet management — `/addwallet` (диалог), `/wallets`, `/removewallet` с балансами
- **Phase 2**: фоновый монитор транзакций + алерты + Docker/Railway деплой
