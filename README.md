# Crypto Watcher Bot

Telegram бот для мониторинга ETH-кошельков. Отслеживает входящие и исходящие транзакции, отправляет алерт если сумма превышает $100 USD.

## Технологии

- Python 3.12, python-telegram-bot 21.x (async, long-polling)
- SQLite (aiosqlite) для хранения кошельков и истории алертов
- Etherscan API для получения транзакций и курса ETH
- Docker + Railway для 24/7 деплоя

## Требования

- Python 3.12+ (для локального запуска без Docker)
- Docker и Docker Compose (для локального Docker запуска)
- Аккаунт Railway (для деплоя)

## Переменные окружения

| Переменная | Источник | Пример |
|---|---|---|
| `BOT_TOKEN` | @BotFather в Telegram | `7123456789:AAF...` |
| `ETHERSCAN_API_KEY` | https://etherscan.io/myapikey (бесплатно) | `ABCDEF1234...` |
| `ALLOWED_USER_IDS` | Свой Telegram ID через @userinfobot | `123456789` |
| `DATABASE_PATH` | Путь к SQLite файлу | `./data/wallets.db` |

## Локальный запуск (без Docker)

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd crypto-watcher-bot

# 2. Создать .env из примера и заполнить значения
cp .env.example .env
# Открыть .env и заполнить BOT_TOKEN, ETHERSCAN_API_KEY, ALLOWED_USER_IDS

# 3. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Запустить бота
python -m bot.main
```

## Локальный запуск через Docker

```bash
# 1. Заполнить .env (см. выше)
cp .env.example .env

# 2. Запустить
docker-compose up

# Остановить
docker-compose down
```

SQLite база данных сохраняется в `./data/wallets.db` на хосте (volume mount).

## Деплой на Railway

Railway обеспечивает 24/7 работу бота.

> **Важно:** без Persistent Volume база данных сбрасывается при каждом перезапуске контейнера. Шаг 4 обязателен.

1. **Залить репозиторий на GitHub**

2. **Создать проект в Railway**
   - Railway Dashboard → New Project → Deploy from GitHub repo
   - Выбрать репозиторий — Railway автоматически найдёт Dockerfile

3. **Добавить переменные окружения**
   - Service → Variables → добавить:
     - `BOT_TOKEN` — токен от @BotFather
     - `ETHERSCAN_API_KEY` — ключ с etherscan.io
     - `ALLOWED_USER_IDS` — свой Telegram user ID
     - `DATABASE_PATH` — установить значение `/app/data/wallets.db`

4. **Создать Persistent Volume** (критично для сохранности данных)
   - Service → Volumes → Add Volume
   - Mount path: `/app/data`
   - Без этого шага SQLite файл исчезает при перезапуске сервиса

5. **Задеплоить**
   - Railway автоматически запустит деплой после добавления переменных
   - Логи: Service → Deployments → View Logs
   - Успешный старт: в логах появится `Monitor polling started`

### Планы Railway

- Free tier: 500 ч/мес — достаточно для теста, но не для 24/7
- Hobby plan ($5/мес): неограниченное время работы — рекомендуется для постоянного мониторинга
