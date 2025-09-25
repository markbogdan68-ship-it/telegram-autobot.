# Telegram Autobot (Reminders, Webhooks, Docker)

Автономный телеграм-бот на `aiogram v3` с напоминаниями (APScheduler) и хранением в SQLite (SQLAlchemy). 
Готов к деплою на Railway / VPS.

## Быстрый старт (мобильный, Railway)
1. Создай бота у @BotFather и скопируй токен.
2. Зайди на GitHub (через телефон), создай **новый репозиторий**, нажми **Add file → Upload files** и залей **все файлы** из этого архива.
3. Зайди на https://railway.app → New Project → Deploy from GitHub → выбери репозиторий.
4. В Railway: Settings → Variables добавь:
   - `TELEGRAM_BOT_TOKEN` = токен от BotFather
   - `TZ=Europe/Berlin`
   - `DATABASE_URL=sqlite+aiosqlite:///./bot.db`
   - `WEBHOOK_SECRET` = случайная строка (например, сгенерируй где угодно)
5. В Settings → Domains получи домен вида `https://<name>.up.railway.app`
6. Добавь переменную `WEBHOOK_URL=https://<name>.up.railway.app/webhook`
7. Деплой. Открой корень `https://<name>.up.railway.app/` — должно быть `ok`. 
   Бот начнёт принимать апдейты по вебхуку.

## Локально (для теста, если есть ноут/ПК)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Команды в Telegram
- `/start` — приветствие
- `/help` — примеры
- `/remind 10мин сделать чай`
- `/remind 18:30 спорт`
- `/remind 2025-10-01 09:00 отчёт`
- `/list` — активные напоминания

## Структура
см. каталог `app/` — основные модули: `handlers`, `scheduler`, `db`, `models`, `webhook`, `main.py`.
