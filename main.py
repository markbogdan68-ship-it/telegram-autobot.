from handlers import router
import os
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from db import init_db


# Небольшой HTTP-сервер для Render
def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()


async def run_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    init_db()

    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
