---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-06-25T20:11:36.682Z"
last_activity: 2026-06-25
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 6
  completed_plans: 5
  percent: 83
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-25)

**Core value:** Автономный 24/7 мониторинг — бот сам замечает крупные движения средств и шлёт алерт без ручного запроса.
**Current focus:** Phase 2 — monitoring, alerts & deployment

## Current Position

Phase: 2
Plan: 2 of 3 complete
Status: In progress — 02-02 done, ready for 02-03
Last activity: 2026-06-25

Progress: [████████░░] 83%

## Accumulated Context

### Decisions

- Init: Python 3.12 + python-telegram-bot v21 (async)
- Init: SQLite + aiosqlite (нет multi-write нагрузки)
- Init: Long-polling (не нужен домен/webhook)
- Init: Etherscan free tier API (5 req/sec, нужен API key)
- Init: Whitelist в .env (не в БД)
- Init: Фиксированный порог $100 USD
- 01-02: Decimal(str(wei)) / Decimal(10**18) — str cast prevents float precision loss in wei_to_eth
- 01-02: Module-level throttle (_last_request float + asyncio.sleep) sufficient for sequential Etherscan requests
- 01-02: validate_address called in get_balance before API call — invalid addr never reaches Etherscan (T-01-04)
- 01-03: wallet_exists() guard before INSERT — explicit duplicate check avoids UNIQUE exception handling (D-03)
- 01-03: asyncio.sleep(0.25) in /wallets loop — no asyncio.gather, throttle safe for Etherscan free tier (D-06, T-01-12)
- 01-03: get_eth_price() called once before wallet loop, not per-wallet — fewer API calls + efficiency
- 02-01: asyncio.create_task in post_init instead of APScheduler — zero new deps (T-02-05)
- 02-01: last_block=0 → fetch current block + return, no historical txns processed on first run
- 02-01: value_wei kept as str in _parse_transactions — Decimal conversion at alert time (02-02)
- 02-01: Decimal('0') fallback for ETH price — won't trigger alerts but won't crash polling loop
- 02-02: strict > threshold (not >=) — $100 exactly does not trigger alert (MON-02)
- 02-02: mark_alert_sent called after send_message, not before — T-02-06 repudiation mitigation
- 02-02: per-tx try/except wraps format+send+mark — one failure never breaks the cycle (T-02-07)

### Blockers/Concerns

- Нужен Etherscan API key (бесплатно на etherscan.io)
- Railway free tier: 500 ч/мес → для 24/7 нужен Hobby plan ($5/мес)
- SQLite на Railway требует persistent volume (иначе БД сбрасывается при перезапуске)
