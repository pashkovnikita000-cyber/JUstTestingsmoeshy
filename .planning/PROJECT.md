# Crypto Watcher Bot

## What This Is

Telegram bot для мониторинга ETH-кошельков. Доверенные пользователи добавляют кошельки по адресу с кастомным именем, бот автоматически отслеживает балансы через Etherscan API и присылает пуш-уведомления о транзакциях на сумму > $100.

## Core Value

Автономный 24/7 мониторинг — бот сам замечает крупные движения средств и шлёт алерт без ручного запроса.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Whitelist доверенных Telegram user ID (env var)
- [ ] Команда /addwallet <address> <name> — добавить ETH-кошелёк с именем
- [ ] Команда /wallets — список кошельков с текущим балансом в ETH и USD
- [ ] Команда /removewallet <address> — удалить кошелёк из слежки
- [ ] Фоновый polling каждые 60 сек — проверка новых транзакций
- [ ] Пуш-алерт в Telegram если входящая или исходящая транзакция > $100 USD
- [ ] SQLite хранение: адрес, имя, user_id, последний проверенный блок
- [ ] Деплой на Railway через Docker

### Out of Scope

- Другие EVM сети (BSC, Polygon) — только ETH Mainnet для v1
- Настраиваемый порог суммы — фиксировано $100
- Публичный доступ — только whitelist
- Web UI — только Telegram

## Context

- Etherscan API: бесплатный тир, 5 req/sec, нужен API ключ
- ETH/USD курс: берём через Etherscan price endpoint (встроен в API)
- Polling стратегия: храним `last_block` на кошелёк, `eth_getBlockByNumber` для новых tx
- Railway: бесплатный тир имеет лимиты (500 ч/мес), для 24/7 нужен Hobby ($5/мес)
- Telegram polling (long-poll) — не нужен webhook и домен

## Constraints

- **Tech stack**: Python 3.12 + python-telegram-bot v21 (async) + aiosqlite
- **API**: Etherscan free tier — rate limit 5 req/sec, нужно throttling
- **Auth**: Whitelist в .env, не в БД — простота важнее гибкости
- **Persistence**: SQLite достаточно для личного бота (< 100 кошельков)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Long-polling вместо webhook | Railway не требует домена/SSL для polling | — Pending |
| SQLite вместо PostgreSQL | Нет multi-write нагрузки, Railway нужен volume для SQLite | — Pending |
| Фиксированный порог $100 | Меньше сложности, можно пересмотреть в v2 | — Pending |
| Etherscan API вместо node RPC | Бесплатно, не нужен full node | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

---
*Last updated: 2026-06-25 after initialization*
