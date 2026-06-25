---
phase: 02-monitoring-alerts-deployment
plan: "02"
subsystem: alert-pipeline
tags: [monitor, alerts, tdd, telegram, dedup]
dependency_graph:
  requires: [02-01]
  provides: [_should_alert, _format_alert, alert-dispatch-in-_check_wallet]
  affects: [bot/monitor.py, tests/test_alerts.py]
tech_stack:
  added: []
  patterns: [TDD-red-green, try-except-per-tx, dedup-before-send, mark-after-send]
key_files:
  created:
    - tests/test_alerts.py
  modified:
    - bot/monitor.py
decisions:
  - "strict > threshold (not >=): $100 exactly does not trigger alert (MON-02 spec)"
  - "is_error skip before _should_alert: saves one DB lookup per failed tx (T-02-09)"
  - "_should_alert before is_alert_sent: avoids DB call for sub-threshold txns"
  - "mark_alert_sent called after send_message, not before: T-02-06 repudiation mitigation"
  - "per-tx try/except wraps format+send+mark: T-02-07 DoS mitigation, one failure never breaks cycle"
metrics:
  duration: "~10 min"
  completed: "2026-06-25"
  tasks_completed: 2
  files_changed: 2
---

# Phase 02 Plan 02: Alert Logic Summary

`_should_alert` + `_format_alert` pure functions (TDD) + full dedup/send/mark dispatch wired into `_check_wallet` — alert pipeline complete, bot now sends Telegram alerts for ETH transactions > $100.

## What Was Built

**bot/monitor.py** — две новые чистые функции + полная логика dispatch:

`_should_alert(value_wei, eth_price, threshold=Decimal("100")) -> bool`
- Строгое сравнение `usd_value > threshold` — $100 ровно не триггерит
- Безопасный fallback при `eth_price=Decimal("0")` — возвращает False без crash

`_format_alert(wallet_name, wallet_address, tx, eth_price) -> str`
- Направление определяется регистро-независимым сравнением `to_addr.lower() == wallet_address.lower()`
- Входящие: `📥 Входящая`, исходящие: `📤 Исходящая`
- Формат: ETH с 4 знаками, USD с 2 знаками и разделителем тысяч
- Markdown: `*wallet_name*`, `` `tx_hash` ``, ссылка `https://etherscan.io/tx/{hash}`

`_check_wallet` — dispatch loop после `update_last_block`:
1. `is_error=True` → skip (T-02-09)
2. `_should_alert` → skip если не превышает порог
3. `await is_alert_sent` → skip если дубль (MON-04)
4. `_format_alert` + `app.bot.send_message(parse_mode="Markdown")`
5. `await mark_alert_sent` — только после успешной отправки (T-02-06)
6. `try/except` на шагах 4-5: ошибка логируется, цикл продолжается (T-02-07)

**tests/test_alerts.py** — 14 новых тестов:
- 6 тестов `_should_alert`: above/below/exactly threshold, zero price, int/str value_wei
- 8 тестов `_format_alert`: incoming/outgoing direction, case-insensitive, wallet_name, tx_hash, etherscan link, ETH 4dp, USD 2dp

## Task Commits

| Task | Description | Hash | Files |
|------|-------------|------|-------|
| 1 | _should_alert + _format_alert (TDD RED/GREEN) | 3c885c3 | bot/monitor.py, tests/test_alerts.py |
| 2 | Wire alert dispatch into _check_wallet | 8691247 | bot/monitor.py |

## Test Results

- **Before plan:** 70 tests passing
- **After plan:** 84 tests passing (+14 new)
  - `test_alerts.py`: 14 tests (_should_alert × 6, _format_alert × 8)
- 0 regressions

## TDD Gate Compliance

| Gate | Evidence | Status |
|------|----------|--------|
| RED | ImportError: cannot import name '_format_alert' from 'bot.monitor' | PASS |
| GREEN | 3c885c3 — 14 tests pass | PASS |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `_check_wallet` stub from 02-01 fully replaced with production dispatch.

## Threat Surface Scan

No new network endpoints or auth paths. All threat mitigations from threat register applied:
- T-02-06 (Repudiation): `mark_alert_sent` called after `send_message` ✓
- T-02-07 (DoS): per-tx `try/except` wraps send+mark ✓
- T-02-08 (Info Disclosure): `chat_id = wallet["user_id"]` from DB, not Telegram context ✓
- T-02-09 (Tampering): `if tx["is_error"]: continue` first in loop ✓

## Self-Check: PASSED

Files created: tests/test_alerts.py ✓
Files modified: bot/monitor.py ✓
Commits verified: 3c885c3 ✓, 8691247 ✓
84 tests pass ✓
