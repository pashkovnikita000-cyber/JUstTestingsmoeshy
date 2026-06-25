---
phase: 01-bot-core-wallet-management
plan: "03"
subsystem: wallet-commands
tags: [python, telegram-bot, conversationhandler, sqlite, aiosqlite, tdd, etherscan]

requires:
  - "01-01: database.py init_db + wallets schema, middleware.py restricted()"
  - "01-02: etherscan.py validate_address, get_balance, get_eth_price"
provides:
  - "bot/database.py: add_wallet, wallet_exists, get_wallets, remove_wallet (user_id-isolated CRUD)"
  - "bot/handlers.py: ConversationHandler /addwallet + /cancel, /wallets, /removewallet, shorten()"
  - "bot/main.py: all wallet handlers registered"
  - "tests/test_database.py: 14 tests covering CRUD + user isolation"
  - "pytest.ini: asyncio_mode = auto"
affects: [phase-02]

tech-stack:
  added: []
  patterns:
    - "ConversationHandler with ASK_ADDRESS/ASK_NAME states (D-01)"
    - "asyncio.sleep(0.25) throttle in /wallets loop — no asyncio.gather (D-06)"
    - "try/except around all Etherscan calls — graceful degrade (T-01-13)"
    - "wallet_exists() guard before INSERT — explicit duplicate check (D-03)"

key-files:
  created:
    - tests/test_database.py
    - pytest.ini
  modified:
    - bot/database.py
    - bot/handlers.py
    - bot/main.py

key-decisions:
  - "wallet_exists() called before INSERT (not catching UNIQUE violation) — more explicit, simpler error path"
  - "asyncio.sleep(0.25) inside /wallets loop; etherscan module throttle still applies — double-safe (D-06)"
  - "get_eth_price() called once before the wallets loop, not per-wallet (T-01-12 + efficiency)"
  - "Graceful degrade on Etherscan failure: wallet saved, balance shows 'temporarily unavailable' (T-01-13)"
  - "shorten() as module-level helper in handlers.py — shared by /addwallet and /wallets"

requirements-completed: [WALLET-01, WALLET-03, WALLET-04, WALLET-05]

tdd-gates:
  red: "81d8f8c — test(01-03): add failing tests"
  green: "20d45ed — feat(01-03): implement CRUD"

duration: 10min
completed: "2026-06-25"
---

# Phase 01 Plan 03: Wallet CRUD Commands Summary

**Full user-facing wallet management: /addwallet (ConversationHandler dialog with validation + balance), /wallets (sequential throttled load, D-04 format), /removewallet — all isolated by user_id, covered by 14 new tests**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-25T18:33:00Z
- **Completed:** 2026-06-25T18:43:00Z
- **Tasks:** 3 (Task 1 TDD: RED + GREEN; Tasks 2+3 feat)
- **Tests added:** 14 (41 total, all passing)
- **Files modified:** 5

## Accomplishments

- CRUD fully isolated by user_id: get/remove never touch another user's wallets (WALLET-05)
- /addwallet dialog: 2-step flow (address → name), invalid address loops back, duplicate shows "Wallet already tracked" without updating (D-03)
- Balance shown immediately after add (specifics): `✅ Added **Name** \`0xABCD...1234\`\nBalance: X ETH ($Y)`
- /wallets: one message, block per wallet (D-04), sequential loop with 0.25s sleep (D-06, T-01-12), price fetched once
- /removewallet: user_id isolation in WHERE clause — cannot delete foreign wallet (WALLET-05)
- All Etherscan calls wrapped in try/except — degrade gracefully without crashing handler (T-01-13)
- All SQL uses ?-placeholders, no f-strings (T-01-11)
- shorten() helper: `0xaaaa...aaaa` (first 6 + `...` + last 4)

## Task Commits

1. **RED — failing tests** — `81d8f8c` (test)
2. **GREEN — database CRUD** — `20d45ed` (feat)
3. **handlers + main** — `4ae72b0` (feat)

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | `81d8f8c` | PASS — ImportError confirmed failure |
| GREEN (feat) | `20d45ed` | PASS — 14/14 tests pass |
| REFACTOR | N/A | No duplication after GREEN |

## Files Modified

- `bot/database.py` — added `wallet_exists`, `add_wallet`, `get_wallets`, `remove_wallet`
- `bot/handlers.py` — added `shorten`, ConversationHandler states+handlers, `/wallets`, `/removewallet`
- `bot/main.py` — registered ConversationHandler + wallets + removewallet
- `tests/test_database.py` — 14 async tests (TDD)
- `pytest.ini` — asyncio_mode = auto for async fixtures

## Deviations from Plan

None — plan executed exactly as written.

## Threat Mitigations Applied

| Threat ID | Status |
|-----------|--------|
| T-01-08 (auth — @restricted) | Mitigated — all 4 entry-point handlers decorated |
| T-01-09 (foreign wallet access) | Mitigated — get/remove filter by user_id in SQL WHERE |
| T-01-10 (invalid address in dialog) | Mitigated — validate_address in ASK_ADDRESS, loops back |
| T-01-11 (SQL injection) | Mitigated — all queries use ? placeholders |
| T-01-12 (Etherscan flood from /wallets) | Mitigated — asyncio.sleep(0.25) between per-wallet requests |
| T-01-13 (Etherscan crash) | Mitigated — try/except in addwallet_name and wallets loop |

## Self-Check: PASSED

Files exist:
- bot/database.py: FOUND
- bot/handlers.py: FOUND
- bot/main.py: FOUND
- tests/test_database.py: FOUND

Commits exist:
- 81d8f8c: FOUND (test RED)
- 20d45ed: FOUND (feat GREEN)
- 4ae72b0: FOUND (feat handlers+main)

Tests: 41 passed, 0 failed

---
*Phase: 01-bot-core-wallet-management*
*Completed: 2026-06-25*
