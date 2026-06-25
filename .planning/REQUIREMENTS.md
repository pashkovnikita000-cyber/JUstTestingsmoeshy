# Requirements — Crypto Watcher Bot

## v1 Requirements

### Auth & Access (AUTH)

- [ ] **AUTH-01**: Только пользователи из whitelist (ALLOWED_USER_IDS в .env) могут взаимодействовать с ботом
- [ ] **AUTH-02**: Бот отвечает "Access denied" всем остальным без объяснений

### Wallet Management (WALLET)

- [ ] **WALLET-01**: Пользователь может добавить ETH-кошелёк командой `/addwallet <address> <name>`
- [ ] **WALLET-02**: Бот валидирует формат ETH-адреса (0x + 40 hex chars)
- [ ] **WALLET-03**: Пользователь может посмотреть список своих кошельков командой `/wallets` (имя, адрес, баланс ETH, баланс USD)
- [ ] **WALLET-04**: Пользователь может удалить кошелёк командой `/removewallet <address>`
- [ ] **WALLET-05**: Каждый пользователь видит только свои кошельки (изоляция по user_id)

### Monitoring (MON)

- [ ] **MON-01**: Фоновый worker проверяет новые транзакции каждые 60 секунд для всех отслеживаемых кошельков
- [ ] **MON-02**: Бот шлёт алерт пользователю при обнаружении транзакции > $100 USD (по курсу на момент tx)
- [ ] **MON-03**: Алерт содержит: имя кошелька, тип (входящая/исходящая), сумму ETH и USD, tx hash, ссылку на Etherscan
- [ ] **MON-04**: Повторные алерты на одну и ту же транзакцию не шлются (дедупликация по tx hash)

### Data & Storage (DATA)

- [ ] **DATA-01**: SQLite БД хранит: кошельки (user_id, address, name), отправленные алерты (tx_hash)
- [ ] **DATA-02**: Последний проверенный блок хранится per-кошелёк для эффективного polling

### Infrastructure (INFRA)

- [ ] **INFRA-01**: Dockerfile для деплоя на Railway
- [ ] **INFRA-02**: Конфигурация через .env (BOT_TOKEN, ETHERSCAN_API_KEY, ALLOWED_USER_IDS)
- [ ] **INFRA-03**: Rate limiting Etherscan API (не более 4 req/sec с буфером)

## v2 (Deferred)

- Настраиваемый порог уведомлений через команду
- Поддержка других EVM сетей (BSC, Polygon)
- Inline-кнопки вместо текстовых команд
- Ежедневный дайджест балансов
- ERC-20 token transfers

## Out of Scope

- Web UI — только Telegram интерфейс
- Публичный доступ — строго whitelist
- Webhook — long-polling достаточно
- PostgreSQL — SQLite достаточно для личного бота

## Traceability

| REQ-ID | Phase |
|--------|-------|
| AUTH-01, AUTH-02 | Phase 1 |
| WALLET-01..05 | Phase 1 |
| DATA-01, DATA-02 | Phase 1 |
| MON-01..04 | Phase 2 |
| INFRA-01..03 | Phase 2 |
