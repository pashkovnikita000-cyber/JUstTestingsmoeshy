# Crypto Watcher Bot

Telegram бот мониторинга ETH-кошельков.

## Stack

- Python 3.12
- python-telegram-bot 21.x (async, long-polling)
- aiosqlite — SQLite для хранения кошельков и алертов
- aiohttp — HTTP клиент для Etherscan API
- Docker + Railway для деплоя

## Structure

```
crypto-watcher-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # точка входа, Application setup
│   ├── config.py        # .env parsing
│   ├── database.py      # SQLite schema + queries
│   ├── etherscan.py     # Etherscan API client
│   ├── handlers.py      # команды /start /addwallet /wallets /removewallet
│   ├── middleware.py    # whitelist auth check
│   └── monitor.py       # фоновый polling worker
├── .planning/           # GSD planning docs
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

## GSD Workflow

Перед правками файлов — запустить GSD команду:
- `/gsd-quick` для мелких фиксов
- `/gsd-execute-phase` для плановой работы

## Environment Variables

```
BOT_TOKEN=           # Telegram bot token from @BotFather
ETHERSCAN_API_KEY=   # https://etherscan.io/myapikey
ALLOWED_USER_IDS=    # comma-separated Telegram user IDs: 123456,789012
DATABASE_PATH=./data/wallets.db
```
