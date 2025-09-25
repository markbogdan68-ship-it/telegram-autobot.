# main.py
import os
import asyncio
import threading
import time
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ---------- ЛОГИРОВАНИЕ ----------
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


# ---------- HTTP для Render ----------
def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    handler = SimpleHTTPRequestHandler
    with TCPServer(("", port), handler) as httpd:
        log.info("HTTP server started on port %s", port)
        httpd.serve_forever()


# ---------- Клавиатуры ----------
def menu_kb(count: int = 0):
    """
    Строим inline-меню.
    1) Счётчик — обновляет сообщение и саму клавиатуру
    2) Помощь — присылает справку
    3) URL-кнопка (пример)
    """
    kb = InlineKeyboardBuilder()
    kb.button(text=f"➕ Счётчик: {count}", callback_data=f"cnt:{count}")
    kb.button(text="ℹ️ Помощь", callback_data="help")
    kb.button(text="🔗 Открыть сайт", url="https://example.com")
    # В первом ряду — счётчик, во втором — две кнопки
    kb.adjust(1, 2)
    return kb.as_markup()


# ---------- БОТ ----------
async def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    bot = Bot(token)
    dp = Dispatcher()

    # /start
    @dp.message(CommandStart())
    async def on_start(m: Message):
        uptime = int(time.time() - START_TS)
        await m.answer(
            f"Я запущен на Render ✅\n"
            f"Доступные команды: /help, /ping, /menu\n"
            f"Uptime: {uptime}s",
            reply_markup=menu_kb(0),
        )

    # /help
    @dp.message(Command("help"))
    async def help_cmd(m: Message):
        await m.answer(
            "Команды:\n"
            "• /ping — проверка\n"
            "• /menu — открыть меню с кнопками\n"
            "• /help — эта справка"
        )

    # /ping
    @dp.message(Command("ping"))
    async def ping_cmd(m: Message):
        await m.answer("pong 🏓")

    # /menu — показать кнопки отдельно
    @dp.message(Command("menu"))
    async def menu_cmd(m: Message):
        await m.answer("Меню:", reply_markup=menu_kb(0))

    # callback: счётчик
    @dp.callback_query(F.data.startswith("cnt:"))
    async def on_counter(cb: CallbackQuery):
        try:
            _, raw = cb.data.split(":")
            n = int(raw) + 1
        except Exception:
            n = 1
        await cb.message.edit_text(
            f"Ты нажал кнопку {n} раз(а).",
            reply_markup=menu_kb(n),
        )
        await cb.answer("Обновил счётчик ✔️")

    # callback: помощь
    @dp.callback_query(F.data == "help")
    async def on_help(cb: CallbackQuery):
        await cb.answer()  # скрыть “часики”
        await cb.message.answer(
            "Это inline-меню:\n"
            "• «Счётчик» обновляет текст и увеличивает число\n"
            "• «Помощь» присылает подсказку\n"
            "• «Открыть сайт» — URL-кнопка"
        )

    log.info("Run polling for bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # поднимем HTTP на фоне, чтобы Render считал сервис живым
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
