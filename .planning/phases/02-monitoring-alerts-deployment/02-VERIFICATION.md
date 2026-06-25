---
phase: 02-monitoring-alerts-deployment
verified: 2026-06-25T21:00:00Z
status: human_needed
score: 3/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Запустить docker-compose up и убедиться, что бот стартует"
    expected: "В логах появляется 'Monitor polling started', бот отвечает на /start"
    why_human: "Docker daemon не запущен на машине верификатора — автоматическая проверка недоступна"
  - test: "Задеплоить на Railway и убедиться, что бот не падает при перезапуске"
    expected: "Бот онлайн после deploy, 'Monitor polling started' в логах Railway, после redeploy продолжает работать"
    why_human: "Railway deployment невозможно верифицировать без живого аккаунта и репо"
  - test: "E2E алерт: добавить кошелёк с известной транзакцией, дождаться цикла, получить алерт в Telegram"
    expected: "Через ~60 сек после добавления кошелька с подходящей транзакцией приходит алерт с именем, направлением, ETH/USD суммой, хешем и ссылкой"
    why_human: "Требует живые токены (BOT_TOKEN, ETHERSCAN_API_KEY) и Telegram-сессию"
---

# Phase 02: Monitoring, Alerts & Deployment — Verification Report

**Phase Goal:** Фоновый воркер отслеживает транзакции и шлёт алерты. Бот задеплоен на Railway.
**Verified:** 2026-06-25T21:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Воркер запускается при старте и проверяет новые tx каждые 60 секунд | ✓ VERIFIED | `_monitor_loop`: `sleep(10)` startup + `while True` + `sleep(60)`; `start_polling(app)` вызывается в `_post_init` через `asyncio.create_task` |
| 2 | При tx > $100 пользователь получает алерт с деталями в течение ~60 сек | ✓ VERIFIED (code) / ? HUMAN (E2E) | `_should_alert` (строгое `>`), `_format_alert` (имя, направление, ETH/USD, hash, ссылка), `app.bot.send_message`; 84/84 тестов проходят |
| 3 | Повторный алерт на ту же транзакцию не отправляется | ✓ VERIFIED | `is_alert_sent` проверяется до отправки; `mark_alert_sent` после; `UNIQUE(tx_hash, user_id)` + `INSERT OR IGNORE`; тесты на идемпотентность проходят |
| 4 | Dockerfile собирается и бот стартует через `docker-compose up` | ? UNCERTAIN | Dockerfile синтаксически корректен, все требуемые конструкции присутствуют; docker-compose.yml корректен; Docker daemon не запущен — сборка не верифицирована автоматически |
| 5 | Railway деплой работает, бот не падает при рестарте | ? HUMAN | `railway.toml` содержит `startCommand = "python -m bot.main"` и `restartPolicyType = "ON_FAILURE"` с 10 retries; реальный деплой требует человека |

**Score:** 3/5 roadmap truths fully verified + 2 требуют человеческой верификации

---

## Required Artifacts

### Plan 02-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `bot/monitor.py` | `start_polling, _check_wallets, _check_wallet, _monitor_loop` | ✓ VERIFIED | Все функции присутствуют и содержательны (127 строк) |
| `bot/database.py` | `get_all_wallets, update_last_block, is_alert_sent, mark_alert_sent` + `sent_alerts` | ✓ VERIFIED | Все 4 функции добавлены; `sent_alerts` создаётся в `init_db()` с `UNIQUE(tx_hash, user_id)` |
| `bot/etherscan.py` | `get_transactions, get_current_block, _parse_transactions, _parse_current_block` | ✓ VERIFIED | Все 4 функции присутствуют и содержательны |
| `tests/test_monitor_db.py` | Тесты для мониторинговых DB-функций | ✓ VERIFIED | 12 тестов, все проходят |
| `tests/test_transactions.py` | Тесты для `_parse_transactions`, `_parse_current_block` | ✓ VERIFIED | 17 тестов, все проходят |

### Plan 02-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `bot/monitor.py` | `_should_alert, _format_alert`, полный dispatch в `_check_wallet` | ✓ VERIFIED | Обе чистые функции присутствуют; `_check_wallet` содержит весь dispatch pipeline |
| `tests/test_alerts.py` | Тесты для `_should_alert` и `_format_alert` | ✓ VERIFIED | 14 тестов, все проходят |

### Plan 02-03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `Dockerfile` | `python:3.12-slim`, non-root user, `/app/data`, `CMD python -m bot.main` | ✓ VERIFIED | Все элементы присутствуют: `FROM python:3.12-slim`, `USER botuser`, `CMD ["python", "-m", "bot.main"]`, `mkdir -p /app/data`, нет `COPY .env` |
| `docker-compose.yml` | volume `./data:/app/data`, `env_file .env` | ✓ VERIFIED | Оба параметра присутствуют; `restart: unless-stopped` |
| `railway.toml` | `builder=DOCKERFILE`, `startCommand`, `restartPolicyType` | ✓ VERIFIED | `builder = "DOCKERFILE"`, `startCommand = "python -m bot.main"`, `restartPolicyType = "ON_FAILURE"`, `restartPolicyMaxRetries = 10` |
| `README.md` | Инструкции локального запуска и Railway деплоя | ✓ VERIFIED | Разделы: локальный запуск, Docker, Railway (5 нумерованных шагов включая Volume), таблица env vars |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `bot/main.py _post_init` | `bot/monitor.py start_polling` | `asyncio.create_task` | ✓ WIRED | `main.py:23-24`: `from bot.monitor import start_polling; start_polling(app)` |
| `monitor.py _check_wallets` | `database.py get_all_wallets` | direct async call | ✓ WIRED | `monitor.py:93`: `wallets = await get_all_wallets()` |
| `monitor.py _check_wallet` | `etherscan.py get_transactions` | direct async call | ✓ WIRED | `monitor.py:68`: `txns = await get_transactions(address, last_block + 1, session=session)` |
| `monitor.py _check_wallet` | `database.py is_alert_sent / mark_alert_sent` | dedup check before/after send | ✓ WIRED | `monitor.py:80`: `await is_alert_sent`; `monitor.py:87`: `await mark_alert_sent` |
| `monitor.py _check_wallet` | `app.bot.send_message` | Telegram bot API | ✓ WIRED | `monitor.py:84-86`: `await app.bot.send_message(chat_id=wallet["user_id"], text=message, parse_mode="Markdown")` |
| `Dockerfile CMD` | `bot/main.py` entry point | `python -m bot.main` | ✓ WIRED | `Dockerfile:22`: `CMD ["python", "-m", "bot.main"]` |
| `docker-compose.yml volume` | `config.DATABASE_PATH` | `./data:/app/data` | ✓ WIRED | Volume mount корректен; README инструктирует `DATABASE_PATH=/app/data/wallets.db` |

---

## Requirements Coverage

| REQ-ID | Plan | Description | Status | Evidence |
|--------|------|-------------|--------|----------|
| MON-01 | 02-01 | Воркер проверяет tx каждые 60 сек | ✓ SATISFIED | `_monitor_loop` с `sleep(60)`; `asyncio.create_task` в `_post_init` |
| MON-02 | 02-02 | Алерт при tx > $100 USD | ✓ SATISFIED | `_should_alert`: строгое `>` Decimal("100"); тесты покрывают граничные случаи |
| MON-03 | 02-02 | Алерт содержит: имя, тип, ETH, USD, hash, ссылку | ✓ SATISFIED | `_format_alert`: все 6 элементов присутствуют в шаблоне |
| MON-04 | 02-02 | Дедупликация по tx hash | ✓ SATISFIED | `is_alert_sent` до отправки; `UNIQUE(tx_hash, user_id)` в БД |
| DATA-02 | 02-01 | Последний блок per-кошелёк | ✓ SATISFIED | `last_block` в схеме `wallets`; `update_last_block` с compound key |
| INFRA-01 | 02-03 | Dockerfile для Railway | ✓ SATISFIED | `Dockerfile` с `python:3.12-slim`, non-root, `/app/data` |
| INFRA-02 | 02-03 | Конфигурация через .env | ✓ SATISFIED | `docker-compose.yml` использует `env_file: .env`; `railway.toml` инструктирует Variables tab |
| INFRA-03 | 02-01 | Rate limiting Etherscan (≤4 req/sec) | ✓ SATISFIED | `_throttle()` вызывается внутри `_get()`; `_MIN_INTERVAL = 0.25` (4 req/sec); все новые endpoint-ы используют `_get()` |

**Замечание:** В `REQUIREMENTS.md` MON-01, DATA-02 и INFRA-03 помечены как `[ ]` (незакрытые). Это расхождение в документации — код реализует все три требования. Рекомендуется обновить чекбоксы.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Все импорты успешны | `python -c "from bot.monitor import start_polling, _should_alert, _format_alert..."` | `All imports OK` | ✓ PASS |
| 84 теста проходят | `pytest -v --tb=short` | `84 passed in 0.19s` | ✓ PASS |
| `_parse_transactions` "No transactions found" → `[]` | тест `test_no_txs_returns_empty_list` | PASSED | ✓ PASS |
| `_parse_current_block` hex → int | тест `test_parses_hex_to_int` | PASSED | ✓ PASS |
| `docker build` | Docker daemon не запущен | N/A | ? SKIP |

---

## Probe Execution

Нет объявленных probes в планах этой фазы. Step 7c: SKIPPED.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `bot/database.py` | 9 | `ponytail:` comment | ℹ️ Info | Намеренное упрощение (single connection per call), задокументировано |
| `bot/etherscan.py` | 23 | `ponytail:` comment | ℹ️ Info | Глобальный lock на throttle — задокументировано с upgrade path |

Нет `TBD`, `FIXME`, `XXX` маркеров. Нет заглушек. `ponytail:` комментарии — намеренные, не долг.

---

## Human Verification Required

### 1. Docker Build & Compose Up

**Test:** Запустить `docker build .` затем `docker-compose up` с заполненным `.env`
**Expected:** Сборка завершается без ошибок; бот стартует, в логах `Monitor polling started`; после `Ctrl+C` файл `./data/wallets.db` присутствует на хосте (volume mount работает)
**Why human:** Docker daemon не был запущен во время верификации

### 2. Railway Deployment

**Test:** Задеплоить репозиторий на Railway согласно README (шаги 1-5), включая Persistent Volume
**Expected:** Деплой успешен; бот онлайн; `Monitor polling started` в логах Railway; после redeploy/restart бот возобновляет работу, кошельки сохранены
**Why human:** Требует аккаунт Railway, GitHub репо и live credentials

### 3. E2E Alert Flow

**Test:** Добавить кошелёк с недавними транзакциями > $100 USD; дождаться до 70 сек
**Expected:** Приходит Telegram-сообщение формата:
```
*WalletName*

📥 Входящая: `0.1234` ETH ($245.67)

Tx: `0xabc...`
https://etherscan.io/tx/0xabc...
```
Второй цикл — повторный алерт НЕ приходит
**Why human:** Требует живые API keys, реальный кошелёк с транзакциями

---

## Gaps Summary

Автоматически верифицируемых gaps нет. Все code-level must-haves выполнены полностью:
- Polling loop: реализован и подключён
- Alert pipeline: реализован (TDD, 84 теста)
- Deduplication: реализован с DB constraint
- Docker/Railway config: все файлы присутствуют и корректны

Два оставшихся пункта требуют человека из-за внешних зависимостей (Docker daemon, Railway account), а не из-за дефектов кода.

---

*Verified: 2026-06-25T21:00:00Z*
*Verifier: Claude (gsd-verifier)*
