# =========================================================
# main.py  — версия с INLINE_FEATURES_V1 (меню + счётчик)
# =========================================================

import os
import asyncio
import threading
import time
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = lambda: None

# ---------- ЛОГИ ----------
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_level = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}.get(LEVEL, logging.INFO)
logging.basicConfig(level=_level, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("bot")
START_TS = time.time()

# ---------- HTTP для Render ----------
def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = TCPServer(("", port), SimpleHTTPRequestHandler)
    log.info("HTTP server on %s", port)
    httpd.serve_forever()

# ---------- Router ----------
router = Router()

# ---------- БАЗОВЫЕ КОМАНДЫ ----------
@router.message(CommandStart())
async def cmd_start(m: Message):
    uptime = int(time.time() - START_TS)
    await m.answer(
        "Я запущен на Render ✅\n"
        "Доступные команды: /help, /ping, /menu, /counter\n"
        f"Uptime: {uptime}s"
    )

@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(
        "Команды:\n"
        "• /ping — проверка\n"
        "• /menu — пример меню\n"
        "• /counter — счётчик с кнопками\n"
        "• /help — эта справка"
    )

@router.message(Command("ping"))
async def cmd_ping(m: Message):
    await m.answer("pong 🏓")

# =========================================================
# INLINE_FEATURES_V1 — МЕНЮ С КНОПКАМИ
# =========================================================
def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Информация", callback_data="menu:info")
    kb.button(text="✉️ Связаться", url="https://t.me/your_username")  # <-- замени!
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(2, 1)
    return kb

@router.message(Command("menu"))
async def show_menu(m: Message):
    await m.answer("Главное меню:", reply_markup=main_menu_kb().as_markup())

@router.callback_query(F.data == "menu:info")
async def menu_info(cq: CallbackQuery):
    await cq.answer()
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu:back")
    await cq.message.edit_text(
        "Это пример информационного экрана.\nЗдесь может быть любой текст.",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "menu:back")
async def menu_back(cq: CallbackQuery):
    await cq.answer("Возврат в меню")
    await cq.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_kb().as_markup()
    )

# =========================================================
# INLINE_FEATURES_V1 — СЧЁТЧИК (+1 / -1 / Сброс)
# =========================================================
def counter_kb(value: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"cnt:-1:{value}")
    kb.button(text="➕", callback_data=f"cnt:+1:{value}")
    kb.button(text="🔄 Сброс", callback_data="cnt:reset:0")
    kb.button(text="⬅️ Назад", callback_data="cnt:back:0")
    kb.adjust(2, 2)
    return kb

@router.message(Command("counter"))
async def start_counter(m: Message):
    start = 0
    await m.answer(f"Счётчик: {start}", reply_markup=counter_kb(start).as_markup())

@router.callback_query(F.data.startswith("cnt:"))
async def on_counter(cq: CallbackQuery):
    try:
        _, action, raw = cq.data.split(":")
        value = int(raw)
    except Exception:
        await cq.answer("Некорректные данные", show_alert=True)
        return

    if action == "+1":
        value += 1
        await cq.answer("Плюс один ✅")
        await cq.message.edit_text(f"Счётчик: {value}", reply_markup=counter_kb(value).as_markup())
    elif action == "-1":
        value -= 1
        await cq.answer("Минус один ✅")
        await cq.message.edit_text(f"Счётчик: {value}", reply_markup=counter_kb(value).as_markup())
    elif action == "reset":
        value = 0
        await cq.answer("Сброшено")
        await cq.message.edit_text(f"Счётчик: {value}", reply_markup=counter_kb(value).as_markup())
    elif action == "back":
        await cq.answer()
        await cq.message.edit_text("Главное меню:", reply_markup=main_menu_kb().as_markup())

# ---------- Запуск ----------
async def run_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)
    log.info("Polling…")
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
