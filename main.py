import os
import asyncio
import threading
import time
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import router            # твои хендлеры лежат тут
from db import init_db                 # инициализация БД

# ==== ЛОГИРОВАНИЕ ====
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_level = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}.get(LEVEL, logging.INFO)

logging.basicConfig(
    level=_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")
START_TS = time.time()


# Небольшой HTTP-сервер, чтобы Render видел живой сервис
def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        log.info("HTTP server is listening on port %s", port)
        httpd.serve_forever()


async def run_bot():
    load_dotenv()  # не мешает, даже если переменные заданы в Render

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    # Инициализация БД
    init_db()

    bot = Bot(token)
    dp = Dispatcher()

    # Подключаем твой router с хендлерами, чтобы не было дублей сообщений
    dp.include_router(router)

    # Глобальный обработчик необработанных ошибок
    async def _on_error(update: object, exception: Exception):
        log.exception("Unhandled error: %s | update=%r", exception, update)
        return True

    dp.errors.register(_on_error)

    log.info("Starting polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # HTTP сервер — в отдельном потоке
    threading.Thread(target=start_http_server, daemon=True).start()
    # Запуск бота
    asyncio.run(run_bot())
