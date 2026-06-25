---
phase: 01-bot-core-wallet-management
verified: 2026-06-25T19:30:00Z
status: human_needed
score: 8/8 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Запустить бота с валидным BOT_TOKEN и ALLOWED_USER_IDS, отправить /start из whitelist"
    expected: "Ответ '✅ Bot is running. Tracking 0 wallets.'"
    why_human: "Требует живое Telegram-соединение с реальным токеном"
  - test: "Написать боту с user_id НЕ из ALLOWED_USER_IDS"
    expected: "Ответ ровно 'Access denied', без дополнительных деталей"
    why_human: "Требует живое Telegram-соединение"
  - test: "/addwallet → валидный ETH-адрес → имя кошелька"
    expected: "Бот подтверждает добавление с балансом: '✅ Added *Name* `0xABCD...1234`\\nBalance: X ETH ($Y)'"
    why_human: "Требует живой Etherscan API key + Telegram-сессия"
  - test: "/wallets при наличии добавленного кошелька"
    expected: "Одно сообщение со списком: имя, сокращённый адрес, баланс ETH и USD для каждого"
    why_human: "Требует живой Etherscan API + Telegram"
  - test: "/removewallet <address> для существующего кошелька"
    expected: "Ответ 'Removed wallet 0xABCD...1234.'; при повторном /wallets — кошелёк отсутствует"
    why_human: "Требует живое Telegram-соединение"
---

# Фаза 01: Bot Core & Wallet Management — Отчёт верификации

**Цель фазы:** Рабочий Telegram бот с whitelist-доступом, управлением кошельками и отображением балансов.
**Верифицировано:** 2026-06-25T19:30:00Z
**Статус:** human_needed
**Повторная верификация:** Нет — первичная верификация

---

## Цель достигнута?

### Наблюдаемые истины (Success Criteria из ROADMAP)

| #  | Истина                                                                 | Статус      | Свидетельство                                                                 |
|----|------------------------------------------------------------------------|-------------|-------------------------------------------------------------------------------|
| SC1 | Пользователь из whitelist получает ответ на /start                    | ✓ VERIFIED  | `@restricted` на `start()`; `count_wallets(user.id)`; ответ "✅ Bot is running. Tracking {n} wallets." |
| SC2 | Пользователь НЕ из whitelist получает "Access denied"                 | ✓ VERIFIED  | `middleware.py:20` — `reply_text("Access denied")`; выход без деталей        |
| SC3 | Пользователь добавляет ETH-адрес+имя — бот подтверждает с балансом    | ✓ VERIFIED  | ConversationHandler ASK_ADDRESS→ASK_NAME; `get_balance()` + `get_eth_price()`; вывод "✅ Added *{name}* `{short}`\nBalance: X ETH ($Y)" |
| SC4 | /wallets показывает список с именами, адресами, балансами ETH и USD   | ✓ VERIFIED  | `wallets()` handler: цикл по `get_wallets(user_id)`, `get_eth_price()` один раз, `asyncio.sleep(0.25)`, форматирование D-04 |
| SC5 | /removewallet удаляет кошелёк из списка                               | ✓ VERIFIED  | `removewallet()` handler: `remove_wallet(user_id, addr)` с WHERE по user_id; ответ "Removed"/"Wallet not found" |

**Счёт:** 5/5 success criteria verified (автоматически)

---

### Обязательные артефакты

| Артефакт              | Назначение                                  | Существует | Субстантивный | Подключён | Статус     |
|-----------------------|---------------------------------------------|------------|---------------|-----------|------------|
| `bot/config.py`       | Парсинг .env: BOT_TOKEN, ALLOWED_USER_IDS   | ✓          | ✓             | ✓         | ✓ VERIFIED |
| `bot/database.py`     | init_db(), CRUD кошельков, изоляция user_id | ✓          | ✓             | ✓         | ✓ VERIFIED |
| `bot/middleware.py`   | restricted() — whitelist-проверка           | ✓          | ✓             | ✓         | ✓ VERIFIED |
| `bot/handlers.py`     | /start, ConversationHandler, /wallets, /removewallet | ✓   | ✓             | ✓         | ✓ VERIFIED |
| `bot/main.py`         | Application setup, регистрация хендлеров    | ✓          | ✓             | ✓         | ✓ VERIFIED |
| `bot/etherscan.py`    | validate_address, get_balance, get_eth_price | ✓         | ✓             | ✓         | ✓ VERIFIED |
| `tests/test_etherscan.py` | 27 тестов на чистые функции            | ✓          | ✓             | N/A       | ✓ VERIFIED |
| `tests/test_database.py`  | 14 тестов CRUD + изоляция              | ✓          | ✓             | N/A       | ✓ VERIFIED |

---

### Верификация ключевых связей (Key Links)

| От                   | До                  | Через                                  | Статус   | Свидетельство                                      |
|----------------------|---------------------|----------------------------------------|----------|----------------------------------------------------|
| `bot/handlers.py`    | `bot/middleware.py` | `@restricted` на всех entry handlers   | ✓ WIRED  | `handlers.py:12` — `from bot.middleware import restricted`; строки 30,41,103,115,149 |
| `bot/handlers.py`    | `bot/database.py`   | count_wallets, add_wallet, get_wallets, remove_wallet | ✓ WIRED | `handlers.py:9` — все 5 функций импортированы и вызываются |
| `bot/main.py`        | `bot/database.py`   | `init_db()` в `_post_init`             | ✓ WIRED  | `main.py:6,21` — `from bot.database import init_db`; `await init_db()` |
| `bot/handlers.py`    | `bot/etherscan.py`  | validate_address, get_balance, get_eth_price | ✓ WIRED | `handlers.py:10` — импорт; вызовы на строках 52,84,85,125,133 |
| `bot/main.py`        | `bot/handlers.py`   | ConversationHandler + CommandHandler'ы | ✓ WIRED  | `main.py:33-45` — все 4 команды зарегистрированы  |
| `bot/etherscan.py`   | Etherscan API       | aiohttp GET `api.etherscan.io`         | ✓ WIRED  | `etherscan.py:13` — `_BASE_URL = "https://api.etherscan.io/api"` |
| `bot/etherscan.py`   | `bot/config.py`     | ETHERSCAN_API_KEY в запросах           | ✓ WIRED  | `etherscan.py:71` — `"apikey": config.ETHERSCAN_API_KEY` |

---

### Трассировка потока данных (Level 4)

| Артефакт           | Данные          | Источник                          | Реальные данные | Статус      |
|--------------------|-----------------|-----------------------------------|-----------------|-------------|
| `handlers.py:start`  | count_wallets | `aiosqlite` SELECT COUNT(*) FROM wallets | ✓ реальный запрос | ✓ FLOWING |
| `handlers.py:wallets` | wallet_list, balance, price | `aiosqlite` SELECT + `aiohttp` Etherscan API | ✓ реальные запросы | ✓ FLOWING |
| `handlers.py:removewallet` | removed | `aiosqlite` DELETE rowcount | ✓ реальное удаление | ✓ FLOWING |

---

### Поведенческие spot-checks

| Проверка                          | Команда                                                        | Результат              | Статус  |
|-----------------------------------|----------------------------------------------------------------|------------------------|---------|
| 41 тест (etherscan + database)    | `python -m pytest tests/ -q`                                   | 41 passed in 0.09s     | ✓ PASS  |
| Импорт bot.main без ошибок        | `python -c "import bot.main; print('OK')"`                     | OK                     | ✓ PASS  |
| Схема содержит last_block         | `grep "last_block" bot/database.py`                            | `last_block INTEGER DEFAULT 0` | ✓ PASS |
| Строка "Access denied" в коде     | `grep "Access denied" bot/middleware.py`                        | строка 20              | ✓ PASS  |
| ConversationHandler зарегистрирован | `grep "ConversationHandler" bot/main.py`                     | строки 3,33            | ✓ PASS  |
| asyncio.gather отсутствует в /wallets | `grep -c "asyncio.gather" bot/handlers.py`                 | 0 (нет)                | ✓ PASS  |

---

### Покрытие требований

| REQ-ID    | План     | Описание                                           | Статус       | Свидетельство                                                      |
|-----------|----------|----------------------------------------------------|--------------|---------------------------------------------------------------------|
| AUTH-01   | 01-01    | Whitelist из ALLOWED_USER_IDS в .env               | ✓ SATISFIED  | `config.py:14-20` — `_parse_user_ids()` → `ALLOWED_USER_IDS: set[int]` |
| AUTH-02   | 01-01    | "Access denied" без объяснений                      | ✓ SATISFIED  | `middleware.py:20` — `reply_text("Access denied")`                 |
| WALLET-01 | 01-03    | Добавление ETH-кошелька через /addwallet            | ✓ SATISFIED  | ConversationHandler + `add_wallet()` — диалог вместо одной команды (D-01) |
| WALLET-02 | 01-02    | Валидация формата 0x+40hex                          | ✓ SATISFIED  | `ADDRESS_RE = ^0x[a-fA-F0-9]{40}$`; 11 тестов                     |
| WALLET-03 | 01-02+03 | /wallets с балансами ETH и USD                      | ✓ SATISFIED  | `wallets()` handler: ETH + USD через Etherscan                     |
| WALLET-04 | 01-03    | /removewallet удаляет кошелёк                       | ✓ SATISFIED  | `removewallet()` + `remove_wallet(user_id, addr)`                   |
| WALLET-05 | 01-03    | Изоляция по user_id                                 | ✓ SATISFIED  | WHERE user_id=? во всех SQL-запросах; 3 теста на изоляцию           |
| DATA-01   | 01-01    | SQLite хранит wallets (user_id, address, name)      | ✓ SATISFIED  | `init_db()` — CREATE TABLE IF NOT EXISTS wallets с полями          |

**Замечание по DATA-02:** REQUIREMENTS.md traceability указывает DATA-02 → Phase 1, однако ROADMAP.md корректно относит DATA-02 к Phase 2 (план 02-01). Поле `last_block INTEGER DEFAULT 0` добавлено в схему в Phase 1 (D-07) — это намеренно. Запись значения в поле происходит в Phase 2 monitoring worker'ом. Противоречие только в traceability таблице REQUIREMENTS.md — не блокер.

**Замечание по REQUIREMENTS.md checkboxes:** AUTH-01, AUTH-02, DATA-01 реализованы, но остаются `[ ]` в REQUIREMENTS.md. Это незакрытый tracking artifact — не влияет на работоспособность кода.

---

### Антипаттерны

| Файл | Строка | Паттерн | Серьёзность | Влияние |
|------|--------|---------|-------------|---------|
| `bot/database.py:9` | 9 | `# ponytail:` комментарий | ℹ️ Info | Намеренное упрощение (одно соединение на вызов); задокументировано; не стаб |
| `bot/etherscan.py:19` | 19 | `# ponytail:` глобальный throttle | ℹ️ Info | Намеренное упрощение; задокументировано с указанием upgrade path |

Долговых маркеров TBD/FIXME/XXX: **0**.

---

### Требуется ручная проверка

#### 1. /start для whitelist-пользователя

**Тест:** Запустить бота с реальным BOT_TOKEN, добавить свой user_id в ALLOWED_USER_IDS, отправить /start
**Ожидается:** Ответ "✅ Bot is running. Tracking 0 wallets."
**Почему человек:** Требует живое Telegram-соединение с реальным токеном

#### 2. /start для не-whitelist-пользователя

**Тест:** Написать боту с user_id НЕ из ALLOWED_USER_IDS
**Ожидается:** Ответ ровно "Access denied", без других деталей, бот не падает
**Почему человек:** Требует живое Telegram-соединение

#### 3. /addwallet — полный диалог с балансом

**Тест:** Ввести /addwallet → валидный ETH-адрес → имя кошелька
**Ожидается:** Подтверждение с текущим балансом "✅ Added *Name* `0xABCD...1234`\nBalance: X ETH ($Y)"
**Почему человек:** Требует живой ETHERSCAN_API_KEY + Telegram-сессия

#### 4. /wallets со списком

**Тест:** Добавить кошелёк, затем /wallets
**Ожидается:** Одно сообщение с блоком на кошелёк: имя, сокращённый адрес, ETH, USD
**Почему человек:** Требует живой Etherscan API + Telegram

#### 5. /removewallet

**Тест:** /removewallet {address}; затем снова /wallets
**Ожидается:** "Removed wallet 0xABCD...1234."; в последующем /wallets кошелёк отсутствует
**Почему человек:** Требует живое Telegram-соединение

---

## Итог

Все 8 задекларированных требований подтверждены анализом кода. Все 5 success criteria из ROADMAP верифицированы статически. 41 тест проходит. Долговых маркеров нет. Архитектурные связи полны.

Единственная блокировка перед статусом `passed` — стандартное ручное тестирование живого Telegram-бота с реальными учётными данными.

---

_Верифицировано: 2026-06-25T19:30:00Z_
_Верификатор: Claude (gsd-verifier)_
