---
phase: 01-bot-core-wallet-management
plan: "01"
subsystem: infra
tags: [python, telegram-bot, sqlite, aiosqlite, dotenv, whitelist]

requires: []
provides:
  - "bot/ package scaffold with importable modules"
  - "config.py: env parsing, ALLOWED_USER_IDS as set[int]"
  - "database.py: init_db() + wallets schema with last_block + count_wallets()"
  - "middleware.py: restricted() decorator — whitelist auth check"
  - "handlers.py: /start command with real DB read"
  - "main.py: Application setup, post_init hook, run_polling entry point"
affects: [01-02, 01-03, phase-02]

tech-stack:
  added:
    - python-telegram-bot==21.5
    - aiosqlite==0.20.0
    - aiohttp==3.9.5
    - python-dotenv==1.0.1
    - pytest==8.3.2
    - pytest-asyncio==0.23.8
  patterns:
    - "restricted() decorator applied to all command handlers (AUTH-02)"
    - "post_init hook in Application.builder() for async DB init"
    - "aiosqlite context manager: async with aiosqlite.connect() as db"
    - "bot.config module as single source of parsed env vars"

key-files:
  created:
    - bot/__init__.py
    - bot/config.py
    - bot/database.py
    - bot/middleware.py
    - bot/handlers.py
    - bot/main.py
    - tests/__init__.py
    - requirements.txt
    - .env.example
    - .gitignore
  modified: []

key-decisions:
  - "post_init hook over asyncio.run() wrapper for init_db — cleaner integration with ptb v21 lifecycle"
  - "ALLOWED_USER_IDS parsed at import time in config.py, not lazily — fail-fast on bad config"
  - "Separate _parse_user_ids() helper in config.py — testable independently"
  - "venv at .venv/ for local dev (Python 3.9 available; Docker uses 3.12 per CLAUDE.md)"

patterns-established:
  - "restricted() applied as decorator at handler definition, not at registration"
  - "All bot modules import config as 'from bot import config' (module reference, not star import)"
  - "aiosqlite open/close per function call — ponytail: no pool needed at personal bot scale"

requirements-completed: [AUTH-01, AUTH-02, DATA-01]

duration: 8min
completed: "2026-06-25"
---

# Phase 01 Plan 01: Walking Skeleton Summary

**python-telegram-bot v21 async bot scaffold with whitelist middleware (restricted decorator), aiosqlite wallets schema (including last_block for Phase 2), and /start reading real DB**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-25T16:33:48Z
- **Completed:** 2026-06-25T16:41:25Z
- **Tasks:** 2 (Task 1 was a human-verify checkpoint — approved before this execution)
- **Files modified:** 10

## Accomplishments

- Walking skeleton proven: Telegram → whitelist check → SQLite read → reply
- wallets table created with `last_block INTEGER DEFAULT 0` (D-07) — Phase 2 reads without migration
- restricted() decorator blocks non-whitelisted users with exactly "Access denied" (AUTH-02)
- `python -m bot.main` entry point works; `import bot.main` has no errors

## Task Commits

1. **Task 1: Package legitimacy audit** — checkpoint approved by user (no commit)
2. **Task 2: Scaffold + config** — `22eb72f` (feat)
3. **Task 3: DB schema + middleware + handlers + main** — `89e359e` (feat)

## Files Created/Modified

- `bot/config.py` — dotenv loading, BOT_TOKEN/ETHERSCAN_API_KEY/DATABASE_PATH/ALLOWED_USER_IDS (AUTH-01)
- `bot/database.py` — init_db() + wallets schema + count_wallets() (DATA-01)
- `bot/middleware.py` — restricted() whitelist decorator (AUTH-02)
- `bot/handlers.py` — /start handler (calls count_wallets, replies with count)
- `bot/main.py` — Application.builder() + post_init(init_db) + run_polling()
- `requirements.txt` — pinned deps: ptb 21.5, aiosqlite 0.20.0, aiohttp 3.9.5, dotenv 1.0.1
- `.env.example` — BOT_TOKEN, ETHERSCAN_API_KEY, ALLOWED_USER_IDS, DATABASE_PATH
- `.gitignore` — excludes .env, .venv/, data/, __pycache__

## Decisions Made

- Used `post_init` hook in ApplicationBuilder for async init_db() — avoids manual asyncio.run() wrapper
- ALLOWED_USER_IDS parsed at module import time for fail-fast behavior
- Local dev uses .venv/ with Python 3.9 (system); Docker will use Python 3.12 per CLAUDE.md

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Python 3.12 not installed locally (CLAUDE.md specifies it for Docker). Created .venv/ with Python 3.9 for local import verification. All code is 3.9-compatible (uses `from __future__ import annotations`). Docker deployment will use 3.12 as intended.

## User Setup Required

Before running the bot:
1. Copy `.env.example` to `.env`
2. Set `BOT_TOKEN` from @BotFather in Telegram
3. Set `ALLOWED_USER_IDS` to your Telegram user ID (get from @userinfobot)
4. (Optional) Set `ETHERSCAN_API_KEY` — needed in Phase 2

Run locally:
```bash
source .venv/bin/activate
python -m bot.main
```

## Next Phase Readiness

- 01-02 (Etherscan client): config.py exports ETHERSCAN_API_KEY, aiohttp installed
- 01-03 (wallet commands): database.py ready for add_wallet/get_wallets/remove_wallet, middleware.py restricted() pattern established
- Phase 2 (monitor): wallets.last_block column exists, no migration needed

---
*Phase: 01-bot-core-wallet-management*
*Completed: 2026-06-25*
