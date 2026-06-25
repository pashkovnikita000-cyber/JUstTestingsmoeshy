---
phase: 02-monitoring-alerts-deployment
plan: "01"
subsystem: polling-worker
tags: [monitor, database, etherscan, asyncio, tdd]
dependency_graph:
  requires: [01-01, 01-02, 01-03]
  provides: [sent_alerts-table, get_all_wallets, update_last_block, is_alert_sent, mark_alert_sent, get_transactions, get_current_block, monitor-polling-loop]
  affects: [bot/database.py, bot/etherscan.py, bot/monitor.py, bot/main.py]
tech_stack:
  added: []
  patterns: [asyncio.create_task, INSERT-OR-IGNORE, compound-key-UPDATE, hex-to-int-parsing]
key_files:
  created:
    - bot/monitor.py
    - tests/test_monitor_db.py
    - tests/test_transactions.py
  modified:
    - bot/database.py
    - bot/main.py
    - bot/etherscan.py
decisions:
  - "asyncio.create_task in post_init instead of APScheduler — zero new deps (T-02-05)"
  - "last_block=0 → fetch current block + return, no historical txns processed on first run"
  - "last_block+1 as startblock — avoids re-processing last seen block"
  - "value_wei kept as str in _parse_transactions — Decimal conversion at alert time (plan 02-02)"
  - "Decimal('0') fallback for ETH price — won't trigger alerts but won't crash polling loop"
metrics:
  duration: "~15 min"
  completed: "2026-06-25"
  tasks_completed: 3
  files_changed: 6
---

# Phase 02 Plan 01: Polling Worker Foundation Summary

Asyncio polling loop with full DB schema + Etherscan txlist integration — фоновый мониторинг кошельков по блокам без новых зависимостей.

## What Was Built

**bot/database.py** расширен четырьмя мониторинговыми функциями и таблицей `sent_alerts`:
- `sent_alerts` таблица с `UNIQUE(tx_hash, user_id)` — идемпотентные INSERT OR IGNORE
- `get_all_wallets()` — все кошельки всех пользователей для polling loop
- `update_last_block(user_id, address, block)` — compound key (user_id + address), кросс-пользовательские обновления невозможны (T-02-03)
- `is_alert_sent()` / `mark_alert_sent()` — проверка и запись отправленных алертов

**bot/etherscan.py** расширен:
- `_parse_transactions()` — чистая функция, "No transactions found" → [], статус "0" с иной причиной → ValueError, blockNumber str→int, isError→bool, from→from_addr
- `_parse_current_block()` — hex string → int с обработкой ошибок
- `get_transactions(address, start_block)` — вызывает txlist API через существующий `_get()` (throttle автоматически)
- `get_current_block()` — eth_blockNumber proxy endpoint

**bot/monitor.py** создан:
- `_check_wallet()` — last_block=0 инициализирует текущим блоком и возвращает без истории; last_block>0 фетчит транзакции, обновляет max_block
- `_check_wallets()` — fetch ETH price один раз, per-wallet try/except (ошибка одного не ломает остальные, T-02-01)
- `_monitor_loop()` — 10s startup delay, 60s цикл, CancelledError re-raise для чистого shutdown
- `start_polling()` — asyncio.create_task, синхронный вызов из post_init

**bot/main.py**: `_post_init` вызывает `start_polling(app)` после `init_db()`.

## Task Commits

| Task | Description | Hash | Files |
|------|-------------|------|-------|
| 1 | DB monitoring schema (TDD) | d9091d7 | bot/database.py, tests/test_monitor_db.py |
| 2 | Etherscan txlist + block (TDD) | 0b9ad39 | bot/etherscan.py, tests/test_transactions.py |
| 3 | monitor.py + main.py wiring | 3d1939c | bot/monitor.py, bot/main.py |

## Test Results

- **Before plan:** 41 tests passing
- **After plan:** 70 tests passing (+29 new)
  - `test_monitor_db.py`: 12 tests (sent_alerts, get_all_wallets, update_last_block, is/mark_alert_sent)
  - `test_transactions.py`: 17 tests (_parse_transactions, _parse_current_block)
- 0 regressions

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| Task 1 RED | ImportError confirmed before implementation | PASS |
| Task 1 GREEN | d9091d7 — 12 tests pass | PASS |
| Task 2 RED | ImportError confirmed before implementation | PASS |
| Task 2 GREEN | 0b9ad39 — 17 tests pass | PASS |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

| File | Location | Description |
|------|----------|-------------|
| bot/monitor.py | `_check_wallet` after update_last_block | Alert dispatch — intentional, added in plan 02-02 |

## Threat Surface Scan

No new network endpoints or auth paths introduced beyond the planned Etherscan txlist and eth_blockNumber calls. Both route through existing `_get()` with throttle (T-02-02 mitigated). SQL in new functions uses `?` placeholders throughout (T-02-03, T-02-04 mitigated).

## Self-Check: PASSED

All files created: bot/monitor.py, tests/test_monitor_db.py, tests/test_transactions.py
All commits verified: d9091d7, 0b9ad39, 3d1939c
