import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import init_db, add_user, count_users, get_sample_users, all_user_ids
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID
    import os
import asyncio
import threading
import time
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------- ЛОГИ ----------
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

# ---------- ГЛОБАЛЬНЫЕ ДАННЫЕ ----------
router = Router()
USERS: set[int] = set()  # собираем user_id тех, кто написал /start (в памяти процесса)

# ---------- КНОПКИ ----------
def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Информация", callback_data="menu:info")
    kb.button(text="✉️ Связаться", callback_data="menu:contact")
    kb.button(text="🧮 Счётчик", callback_data="menu:counter")
    kb.adjust(2, 1)
    return kb

def counter_kb(value: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"cnt:-1:{value}")
    kb.button(text="➕", callback_data=f"cnt:+1:{value}")
    kb.button(text="🔄 Сброс", callback_data="cnt:reset:0")
    kb.button(text="⬅️ Назад", callback_data="cnt:back:0")
    kb.adjust(2, 2)
    return kb

# ---------- КОМАНДЫ ----------
@router.message(CommandStart())
async def cmd_start(m: Message):
    USERS.add(m.from_user.id)
    await m.answer(
        "Я запущен на Render ✅\nДоступные команды: /help, /ping, /menu, /feedback",
        reply_markup=main_menu_kb().as_markup()
    )

@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(
        "Команды:\n"
        "• /ping — проверка\n"
        "• /menu — меню с кнопками\n"
        "• /feedback <текст> — написать админу\n"
        "• /broadcast <текст> — рассылка (только админ)\n"
        "• /users — сколько пользователей (только админ)"
    )

@router.message(Command("ping"))
async def cmd_ping(m: Message):
    await m.answer("pong 🏓")

@router.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Главное меню:", reply_markup=main_menu_kb().as_markup())

# ---------- CALLBACKS МЕНЮ ----------
@router.callback_query(F.data == "menu:info")
async def menu_info(cq: CallbackQuery):
    await cq.answer()
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu:back")
    kb.adjust(1)
    up = int(time.time() - START_TS)
    await cq.message.edit_text(
        f"Информация:\n• Аптайм процесса: ~{up} сек.",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "menu:contact")
async def menu_contact(cq: CallbackQuery):
    await cq.answer("Пиши командой /feedback <твой текст>")
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu:back")
    kb.adjust(1)
    await cq.message.edit_text(
        "Напиши админу: /feedback Привет! Нужна помощь...",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "menu:counter")
async def menu_counter(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_text(
        "Счётчик: 0",
        reply_markup=counter_kb(0).as_markup()
    )

@router.callback_query(F.data == "menu:back")
async def menu_back(cq: CallbackQuery):
    await cq.answer("Возврат в меню")
    await cq.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_kb().as_markup()
    )

# ---------- СЧЁТЧИК ----------
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
    elif action == "-1":
        value -= 1
        await cq.answer("Минус один ✅")
    elif action == "reset":
        value = 0
        await cq.answer("Сброшено")
    elif action == "back":
        await cq.answer()
        await cq.message.edit_text(
            "Главное меню:",
            reply_markup=main_menu_kb().as_markup()
        )
        return

    await cq.message.edit_text(
        f"Счётчик: {value}",
        reply_markup=counter_kb(value).as_markup()
    )

# ---------- АДМИН/РАССЫЛКА ----------
def is_admin(user_id: int) -> bool:
    try:
        admin_id = int(os.getenv("ADMIN_ID", "0"))
    except Exception:
        admin_id = 0
    return admin_id and user_id == admin_id

@router.message(Command("users"))
async def cmd_users(m: Message):
    if not is_admin(m.from_user.id):
        return await m.answer("Команда только для админа.")

    total = count_users()
    if total == 0:
        return await m.answer("Пока нет ни одного пользователя.")

    sample = get_sample_users(10)
    preview = ", ".join(map(str, sample))
    more = f"\n…и ещё {total-10}" if total > 10 else ""
    await m.answer(f"Пользователей: {total}\n{preview}{more}")
@router.message(Command("broadcast")))
async def cmd_broadcast(m: Message):
    if not is_admin(m.from_user.id):
        return await m.answer("Команда только для админа.")

    parts = m.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await m.answer("Использование: /broadcast ТЕКСТ_СООБЩЕНИЯ")

    text = parts[1].strip()
    ok, fail = 0, 0

    for uid in all_user_ids():
        try:
            await m.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1

    await m.answer(f"Готово. Отправлено: {ok}. Ошибок: {fail}.")
# ---------- ОБРАТНАЯ СВЯЗЬ ----------
@router.message(Command("feedback"))
async def cmd_feedback(m: Message):
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Напиши: /feedback твой текст")
        return
    admin_raw = os.getenv("ADMIN_ID")
    if not admin_raw:
        await m.answer("Админ не настроен.")
        return
    try:
        admin_id = int(admin_raw)
    except Exception:
        await m.answer("ADMIN_ID задан некорректно.")
        return

    txt = parts[1]
    me = m.from_user
    header = f"✉️ Сообщение от @{me.username or 'user'} (id {me.id}):"
    try:
        await m.bot.send_message(admin_id, f"{header}\n\n{txt}")
        await m.answer("Отправил администратору. Спасибо!")
    except Exception as e:
        log.error("feedback send failed: %s", e)
        await m.answer("Не удалось отправить администратору.")

# ---------- HTTP-СЕРВЕР ДЛЯ RENDER ----------
def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        log.info("HTTP server on :%s", port)
        httpd.serve_forever()

# ---------- ЗАПУСК ----------
async def run_bot():
    # ... у тебя тут load_dotenv(), token и т.д.
    init_db()  # <-- ДО dp.start_polling(...)
    # dp = Dispatcher(), include_router(...), и т.п.
    await dp.start_polling(bot)
    async def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
