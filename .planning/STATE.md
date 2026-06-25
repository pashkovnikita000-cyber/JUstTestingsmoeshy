---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: initialized
stopped_at: null
last_updated: "2026-06-25"
last_activity: 2026-06-25
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 6
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-25)

**Core value:** Автономный 24/7 мониторинг — бот сам замечает крупные движения средств и шлёт алерт без ручного запроса.
**Current focus:** Phase 01 — Bot Core & Wallet Management

## Current Position

Phase: 01 (Bot Core & Wallet Management) — READY
Plan: 1 of 3
Status: Not started
Last activity: 2026-06-25

Progress: [░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

- Init: Python 3.12 + python-telegram-bot v21 (async)
- Init: SQLite + aiosqlite (нет multi-write нагрузки)
- Init: Long-polling (не нужен домен/webhook)
- Init: Etherscan free tier API (5 req/sec, нужен API key)
- Init: Whitelist в .env (не в БД)
- Init: Фиксированный порог $100 USD

### Blockers/Concerns

- Нужен Etherscan API key (бесплатно на etherscan.io)
- Railway free tier: 500 ч/мес → для 24/7 нужен Hobby plan ($5/мес)
- SQLite на Railway требует persistent volume (иначе БД сбрасывается при перезапуске)
