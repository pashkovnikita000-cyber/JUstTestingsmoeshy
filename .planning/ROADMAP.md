# Roadmap — Crypto Watcher Bot

**2 phases** | **13 requirements** | Vertical MVP

---

## Phase 1: Bot Core & Wallet Management

**Goal:** Рабочий Telegram бот с whitelist-доступом, управлением кошельками и отображением балансов.

**Mode:** mvp

**Requirements:** AUTH-01, AUTH-02, WALLET-01, WALLET-02, WALLET-03, WALLET-04, WALLET-05, DATA-01

**Success Criteria:**
1. Пользователь из whitelist может запустить бота и получить ответ на /start
2. Пользователь НЕ из whitelist получает "Access denied"
3. Пользователь добавляет ETH-адрес с именем — бот подтверждает и показывает текущий баланс
4. /wallets показывает список с именами, адресами, балансами ETH и USD
5. /removewallet удаляет кошелёк из списка

**Plans:** 3/3 plans complete

Plans:
- [ ] `01-01-PLAN.md` — Walking Skeleton: scaffold, config, SQLite schema (wallets + last_block), whitelist middleware, /start
- [ ] `01-02-PLAN.md` — Etherscan client (TDD): validate_address, getBalance, ETH/USD price, троттлинг
- [ ] `01-03-PLAN.md` — Wallet commands: /addwallet (диалог), /wallets, /removewallet + изоляция по user_id

---

## Phase 2: Monitoring, Alerts & Deployment

**Goal:** Фоновый воркер отслеживает транзакции и шлёт алерты. Бот задеплоен на Railway.

**Mode:** mvp

**Requirements:** MON-01, MON-02, MON-03, MON-04, DATA-02, INFRA-01, INFRA-02, INFRA-03

**Success Criteria:**
1. Воркер запускается при старте и проверяет новые tx каждые 60 секунд
2. При tx > $100 пользователь получает алерт с деталями в течение ~60 сек
3. Повторный алерт на ту же транзакцию не отправляется
4. Dockerfile собирается и бот стартует через `docker-compose up`
5. Railway деплой работает, бот не падает при рестарте

**Plans:** 3 plans

Plans:
- [x] `02-01-PLAN.md` — Polling worker: sent_alerts DB schema, Etherscan txlist + get_current_block, asyncio monitor loop, main.py wiring
- [ ] `02-02-PLAN.md` — Alert logic: _should_alert/$100 threshold, _format_alert (TDD), dedup+send wired into _check_wallet
- [ ] `02-03-PLAN.md` — Deployment: Dockerfile (python:3.12-slim, non-root), docker-compose.yml, railway.toml, README

---

## Coverage Check

| REQ-ID | Phase | Plan |
|--------|-------|------|
| AUTH-01 | 1 | 01-01 |
| AUTH-02 | 1 | 01-01 |
| WALLET-01 | 1 | 01-03 |
| WALLET-02 | 1 | 01-02 |
| WALLET-03 | 1 | 01-02 + 01-03 |
| WALLET-04 | 1 | 01-03 |
| WALLET-05 | 1 | 01-03 |
| DATA-01 | 1 | 01-01 |
| DATA-02 | 2 | 02-01 |
| MON-01 | 2 | 02-01 |
| MON-02 | 2 | 02-02 |
| MON-03 | 2 | 02-02 |
| MON-04 | 2 | 02-02 |
| INFRA-01 | 2 | 02-03 |
| INFRA-02 | 1 | 01-01 (.env config заложен) + 2 | 02-03 |
| INFRA-03 | 2 | 02-01 |

All 13 v1 requirements covered ✓
