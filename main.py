import os
import asyncio
import threading
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from handlers import router
from db import init_db


# ---------- Логи ----------
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LEVEL, logging.INFO))
log = logging.getLogger("bot")


# ---------- HTTP для Render ----------
def start_http_server():
    port = int(os.environ.get("PORT", 8080))

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            # тише в логах
            pass

    with TCPServer(("", port), Handler) as httpd:
        log.info(f"HTTP server on 0.0.0.0:{port}")
        httpd.serve_forever()


# ---------- Запуск бота ----------
async def run_bot():
    load_dotenv()  # подхватываем .env и переменные окружения Render
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    # Инициализируем БД
    init_db()

    # aiogram v3
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token)

    log.info("Start polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # HTTP в фоне — чтобы Render считал сервис «живым»
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
