---
phase: 01-bot-core-wallet-management
plan: "02"
subsystem: etherscan-client
tags: [python, etherscan, aiohttp, decimal, tdd, validation, throttle]

requires:
  - "01-01: config.py with ETHERSCAN_API_KEY, aiohttp in requirements.txt"
provides:
  - "bot/etherscan.py: validate_address, get_balance, get_eth_price"
  - "tests/test_etherscan.py: 27 passing tests for pure functions"
affects: [01-03, phase-02]

tech-stack:
  added: []
  patterns:
    - "Decimal arithmetic for money values (no float)"
    - "Module-level throttle via time.monotonic() + asyncio.sleep (>=0.25s)"
    - "_parse_*/wei_to_eth as pure functions — unit-testable without network"
    - "validate_address before any API call (T-01-04)"
    - "_get() helper factors shared aiohttp GET + throttle"

key-files:
  created:
    - bot/etherscan.py
    - tests/test_etherscan.py
  modified: []

key-decisions:
  - "Decimal(str(wei)) / Decimal(10**18) — str cast prevents float precision loss"
  - "Module-level _last_request float for throttle — sufficient for sequential requests (D-06)"
  - "_get() helper owns throttle + apikey injection — callers pass only module/action params"
  - "Session parameter on get_balance/get_eth_price — allows reuse of caller's ClientSession for batching"

requirements-completed: [WALLET-02, WALLET-03]

tdd-gates:
  red: "a472d6c — test(01-02): add failing tests"
  green: "379b513 — feat(01-02): implement Etherscan client"
  refactor: "N/A — code was clean after GREEN"

duration: 5min
completed: "2026-06-25"
---

# Phase 01 Plan 02: Etherscan Client Summary

**Isolated, fully-tested Etherscan client: address validation via regex, wei→ETH conversion with Decimal, balance and price fetchers with 0.25s throttle — TDD RED/GREEN/REFACTOR**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-25T18:00:00Z
- **Completed:** 2026-06-25T18:06:25Z
- **Tasks:** 1 feature (TDD: RED + GREEN)
- **Tests:** 27 passing, 0 failing

## Accomplishments

- `validate_address` with `ADDRESS_RE = ^0x[a-fA-F0-9]{40}$` — covers empty, short, long, no-prefix, invalid chars (WALLET-02, T-01-04)
- `wei_to_eth` — Decimal arithmetic, accepts int or str, no float precision risk
- `_parse_balance` / `_parse_price` — raise `ValueError` on bad API responses (T-01-06)
- `get_balance` / `get_eth_price` — async aiohttp GET with 0.25s module-level throttle (D-06, T-01-05)
- Address validated before any Etherscan call — invalid addr never reaches the API (T-01-04)
- `_get()` helper deduplicates URL construction + apikey injection

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | `a472d6c` | PASS — ImportError confirmed failure |
| GREEN (feat) | `379b513` | PASS — 27/27 tests pass |
| REFACTOR | N/A | No duplication found after GREEN |

## Task Commits

1. **RED — failing tests** — `a472d6c` (test)
2. **GREEN — implementation** — `379b513` (feat)

## Files Created

- `bot/etherscan.py` — exports `validate_address`, `get_balance`, `get_eth_price` (+ `wei_to_eth`, `_parse_balance`, `_parse_price`)
- `tests/test_etherscan.py` — 27 tests: 11 validate_address, 6 wei_to_eth, 5 _parse_balance, 5 _parse_price

## Decisions Made

- Decimal cast via `Decimal(str(wei))` — avoids float representation errors for large wei values
- Module-level `_last_request: float` for throttle — simplest correct approach for sequential requests; per-wallet locks only if concurrent fetching is added later
- `session` parameter on async functions — caller (handlers.py) can pass one `ClientSession` for the full /wallets batch load, saving connection overhead

## Deviations from Plan

None — plan executed exactly as written.

## Threat Mitigations Applied

| Threat ID | Status |
|-----------|--------|
| T-01-04 (address injection) | Mitigated — `validate_address` called in `get_balance` before API call |
| T-01-05 (rate limit / key ban) | Mitigated — `_throttle()` enforces >=0.25s between requests |
| T-01-06 (malformed API response) | Mitigated — parsers raise `ValueError` on `status != "1"` or missing fields |
| T-01-07 (key in logs) | Accepted — free-tier key, apikey injected only in params dict, not logged |

## Next Phase Readiness

- 01-03 (wallet commands): `validate_address`, `get_balance`, `get_eth_price` all exported and tested
- `get_balance` / `get_eth_price` accept optional `session` — handlers.py can share one `ClientSession` for sequential /wallets load with built-in throttle

---
*Phase: 01-bot-core-wallet-management*
*Completed: 2026-06-25*
