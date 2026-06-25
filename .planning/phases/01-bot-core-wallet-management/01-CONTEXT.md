# Phase 1: Bot Core & Wallet Management - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Рабочий Telegram бот с whitelist-доступом, multi-step добавлением кошельков через диалог, отображением балансов ETH/USD, и SQLite хранением (включая last_block для Phase 2 polling).

Покрывает: AUTH-01, AUTH-02, WALLET-01, WALLET-02, WALLET-03, WALLET-04, WALLET-05, DATA-01.

</domain>

<decisions>
## Implementation Decisions

### /addwallet — Команда добавления кошелька

- **D-01:** Формат — multi-step диалог. Бот сначала просит адрес, затем имя отдельными сообщениями. Реализация через `ConversationHandler` из python-telegram-bot.
- **D-02:** Отмена — команда `/cancel` в любой момент диалога завершает добавление без сохранения.
- **D-03:** Дублирующийся адрес → ошибка "Wallet already tracked" (без обновления существующей записи).

### /wallets — Отображение кошельков

- **D-04:** Формат вывода — одно сообщение со всем списком. Каждый кошелёк как отдельный блок:
  ```
  **Name** `0xABCD...1234`
  Balance: 1.23 ETH ($3,456)
  ```
- **D-05:** Пустой список → `"No wallets tracked. Use /addwallet"`
- **D-06:** Загрузка балансов из Etherscan при /wallets — последовательно с тротлингом 0.25 сек между запросами (не asyncio.gather, чтобы не превысить лимит 5 req/sec).

### SQLite Schema

- **D-07:** Поле `last_block INTEGER DEFAULT 0` добавляется в таблицу `wallets` уже в Phase 1 (01-01-PLAN.md). Phase 2 читает поле без миграции.
- **D-08:** Таблица `sent_alerts` (дедупликация по tx_hash) создаётся в Phase 2 вместе с monitor логикой — в Phase 1 не нужна.

### Ранее зафиксированные решения (из STATE.md)

- **D-09:** Python 3.12 + python-telegram-bot v21 (async) + aiosqlite
- **D-10:** Long-polling, не webhook (Railway не требует домена/SSL)
- **D-11:** Whitelist в .env (ALLOWED_USER_IDS), не в БД
- **D-12:** Etherscan free tier (5 req/sec, нужен API key)
- **D-13:** Фиксированный порог $100 (не настраивается в v1)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope & decisions
- `.planning/PROJECT.md` — описание проекта, constraints, key decisions таблица
- `.planning/REQUIREMENTS.md` — полный список требований с ID (AUTH-*, WALLET-*, DATA-*)
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, разбивка по планам (01-01..01-03)

### Library docs
- python-telegram-bot v21 ConversationHandler — для multi-step /addwallet диалога
- aiosqlite — async SQLite API для database.py

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Нет существующего кода — чистый старт.

### Established Patterns
- Структура файлов задана в CLAUDE.md: `bot/main.py`, `bot/config.py`, `bot/database.py`, `bot/etherscan.py`, `bot/handlers.py`, `bot/middleware.py`, `bot/monitor.py`.
- Whitelist middleware — отдельный файл `middleware.py`, применяется ко всем хендлерам.

### Integration Points
- `handlers.py` зависит от `database.py` (CRUD кошельков) и `etherscan.py` (балансы при /wallets и после /addwallet)
- `main.py` регистрирует ConversationHandler для /addwallet и обычные CommandHandler для /wallets, /removewallet, /start

</code_context>

<specifics>
## Specific Ideas

- После успешного /addwallet бот должен сразу показать баланс добавленного кошелька (подтверждение + первый снимок состояния).
- Адрес в сообщениях показывать сокращённо: первые 6 + последние 4 символа (`0xABCD...1234`) для читаемости.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1 — Bot Core & Wallet Management*
*Context gathered: 2026-06-25*
