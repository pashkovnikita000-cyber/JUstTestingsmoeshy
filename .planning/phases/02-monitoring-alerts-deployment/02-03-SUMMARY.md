---
phase: 02-monitoring-alerts-deployment
plan: "03"
subsystem: infra
tags: [docker, railway, sqlite, deployment, python]

requires:
  - phase: 02-01
    provides: monitor.py polling loop entry point (python -m bot.main)
  - phase: 02-02
    provides: full bot feature set ready to containerize

provides:
  - Dockerfile (python:3.12-slim, non-root botuser, /app/data volume point)
  - docker-compose.yml (local dev with .env + ./data:/app/data volume)
  - railway.toml (Railway v2 build + deploy config)
  - README.md (local setup, docker run, Railway deploy steps with volume config)

affects: [deployment, ops, railway-setup]

tech-stack:
  added: [Docker, docker-compose, Railway v2]
  patterns:
    - Non-root container user (botuser UID 1000) for security
    - Cache-friendly Dockerfile layer order (deps before source)
    - Secrets injected at runtime via env_file / Railway Variables — never baked into image
    - Persistent volume at /app/data for SQLite on Railway

key-files:
  created:
    - Dockerfile
    - docker-compose.yml
    - railway.toml
    - README.md
  modified: []

key-decisions:
  - "python:3.12-slim as base — matches project Python version, minimal footprint"
  - "Non-root botuser (UID 1000) — T-02-11 elevation of privilege mitigation"
  - "No COPY .env / no ENV secrets in Dockerfile — T-02-10 info disclosure mitigation"
  - "Volume ./data:/app/data in docker-compose for SQLite persistence in local dev"
  - "Railway Persistent Volume documented in README (cannot be declared in railway.toml)"
  - "restartPolicyType = ON_FAILURE with 10 retries in railway.toml"

requirements-completed: [INFRA-01, INFRA-02]

duration: 15min
completed: 2026-06-25
---

# Phase 2 Plan 03: Docker + Railway Deployment Summary

**python:3.12-slim container with non-root user, /app/data volume mount, Railway v2 config, and full README covering local and Railway deployment**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-25T20:11:36Z
- **Completed:** 2026-06-25T20:30:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint:human-verify)
- **Files modified:** 4

## Accomplishments

- Dockerfile builds bot into python:3.12-slim image with non-root botuser, cache-optimized layers, /app/data directory for SQLite
- docker-compose.yml enables `docker-compose up` local dev with env_file and volume persistence
- railway.toml configures Railway v2 automated build from Dockerfile + ON_FAILURE restart policy
- README.md covers local bare-metal setup, local Docker run, and full Railway deploy walkthrough including critical Persistent Volume step

## Task Commits

1. **Task 1: Dockerfile + docker-compose.yml** — `01b9c0f` (chore)
2. **Pre-checkpoint: railway.toml + README.md** — `d567b7c` (chore)

## Files Created/Modified

- `Dockerfile` — python:3.12-slim, pip layer cached, source copy, /app/data mkdir, non-root botuser, CMD python -m bot.main
- `docker-compose.yml` — local dev service: build context, env_file .env, volume ./data:/app/data, restart unless-stopped
- `railway.toml` — builder=DOCKERFILE, startCommand=python -m bot.main, restartPolicyType=ON_FAILURE, maxRetries=10
- `README.md` — prerequisites, local setup, local Docker, Railway deploy (numbered steps), env vars table

## Decisions Made

- `railway.toml` uses `restartPolicyType = "ON_FAILURE"` with 10 retries — covers transient network errors without infinite restart loops
- Railway Persistent Volume not declarable in railway.toml (Railway limitation) — documented as critical manual step in README
- Dockerfile `mkdir -p /app/data` redundant with database.py `os.makedirs` but ensures directory exists with correct owner before `USER botuser` switch

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Railway deployment requires manual steps:
1. Push repo to GitHub
2. Railway Dashboard → New Project → Deploy from GitHub repo
3. Variables tab: set `BOT_TOKEN`, `ETHERSCAN_API_KEY`, `ALLOWED_USER_IDS`, `DATABASE_PATH=/app/data/wallets.db`
4. Volumes tab: Add Volume, mount path `/app/data` — **critical for SQLite persistence, DB resets on restart without this**
5. Deploy triggers automatically on push

Environment variables source:
- `BOT_TOKEN` — @BotFather in Telegram
- `ETHERSCAN_API_KEY` — https://etherscan.io/myapikey (free account)
- `ALLOWED_USER_IDS` — own Telegram user ID via @userinfobot

## Next Phase Readiness

Phase 2 is complete. The bot is fully containerized and ready for Railway deployment.

- All core features ship: wallet add/remove/list, balance check, 24/7 ETH transaction monitoring, alert dispatch
- Threat mitigations T-02-10 (no secrets in image) and T-02-11 (non-root user) implemented
- T-02-12 (DB persistence) documented — requires user to add Railway Persistent Volume
- No further development planned; move to production deployment via Railway

---
*Phase: 02-monitoring-alerts-deployment*
*Completed: 2026-06-25*
