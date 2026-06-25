---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
last_updated: "2026-06-25T18:44:15.384Z"
last_activity: 2026-06-25
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-25)

**Core value:** Автономный 24/7 мониторинг — бот сам замечает крупные движения средств и шлёт алерт без ручного запроса.
**Current focus:** Phase 01 — bot-core-wallet-management

## Current Position

Phase: 01 (bot-core-wallet-management) — COMPLETE
Plan: 3 of 3 (all complete)
Status: Phase complete — ready for verification
Last activity: 2026-06-25 -- 01-03 wallet CRUD + commands completed

Progress: [██████████] 100%

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

### Blockers/Concerns

- Нужен Etherscan API key (бесплатно на etherscan.io)
- Railway free tier: 500 ч/мес → для 24/7 нужен Hobby plan ($5/мес)
- SQLite на Railway требует persistent volume (иначе БД сбрасывается при перезапуске)
