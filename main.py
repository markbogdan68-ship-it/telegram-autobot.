import os
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from db import init_db  # абсолютные импорты

# Небольшой HTTP-сервер, чтобы Render видел "живой" порт ($PORT)
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

    @dp.message(CommandStart())
    async def on_start(m: Message):
        await m.answer("Я запущен на Render ✅")

    @dp.message(F.text)
    async def echo(m: Message):
        await m.answer(m.text)

    await dp.start_polling(bot)

if __name__ == "__main__":
    # поднимем HTTP на фоне, чтобы web-сервис на Render не ругался
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
