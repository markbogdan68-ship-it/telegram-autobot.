# -*- coding: utf-8 -*-
"""
Полностью автономный Telegram-бот (aiogram v3) в одном файле:
- /start /help /ping /menu /counter
- База SQLite (SQLAlchemy 2.x): хранит пользователей
- Админ-команды: /users /broadcast <текст> /feedback <текст>
- Inline-кнопки, счётчик, меню
- Фоновый HTTP-сервер для Render (держит инстанс активным)
Переменные окружения:
  TELEGRAM_TOKEN – токен бота (обязательно)
  ADMIN_ID       – Telegram ID админа (число, опционально)
  LOG_LEVEL      – уровень логов (INFO/DEBUG/…)
"""
from __future__ import annotations

import os
import asyncio
import threading
import logging
import time
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from typing import Optional, List

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== SQLAlchemy (в одном файле) =====
from sqlalchemy import create_engine, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, default="")


DB_URL = "sqlite:///./db.sqlite3"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def add_user(tg_id: int, username: Optional[str]) -> None:
    with SessionLocal() as s:
        u = s.execute(select(User).where(User.tg_id == tg_id)).scalar_one_or_none()
        if not u:
            s.add(User(tg_id=tg_id, username=(username or "")[:100]))
            s.commit()


def count_users() -> int:
    with SessionLocal() as s:
        return s.query(User).count()


def get_all_users_ids() -> List[int]:
    with SessionLocal() as s:
        rows = s.query(User.tg_id).all()
        return [r[0] for r in rows]


# ===== Логи =====
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")


# ===== Inline-меню и хэндлеры =====
router = Router()
ADMIN_ID = os.getenv("ADMIN_ID")  # может быть пусто


def is_admin(user_id: int) -> bool:
    if not ADMIN_ID:
        return False
    try:
        return int(ADMIN_ID) == int(user_id)
    except Exception:
        return False


def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Информация", callback_data="menu:info")
    kb.button(text="✉️ Связаться", url="https://t.me/your_username")  # замени на свой @username
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(2, 1)
    return kb


@router.message(CommandStart())
async def on_start(m: Message):
    add_user(m.from_user.id, m.from_user.username)
    await m.answer(
        "Я запущен на Render ✅\n"
        "Доступные команды: /help, /ping, /menu, /counter, /users, /broadcast, /feedback"
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(
        "Команды:\n"
        "• /ping — проверка\n"
        "• /menu — меню с кнопками\n"
        "• /counter — счётчик\n"
        "• /users — число пользователей (админ)\n"
        "• /broadcast <текст> — рассылка (админ)\n"
        "• /feedback <текст> — написать админу"
    )


@router.message(Command("ping"))
async def cmd_ping(m: Message):
    await m.answer("pong 🏓")


@router.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Главное меню:", reply_markup=main_menu_kb().as_markup())


@router.callback_query(F.data == "menu:info")
async def cb_menu_info(cq: CallbackQuery):
    await cq.answer()
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В меню", callback_data="menu:back")
    await cq.message.edit_text(
        "Это пример информационного экрана.\nЗдесь может быть любой текст.",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "menu:back")
async def cb_menu_back(cq: CallbackQuery):
    await cq.answer("Возврат в меню")
    await cq.message.edit_text("Главное меню:", reply_markup=main_menu_kb().as_markup())


# ----- Счётчик -----
def counter_kb(value: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"cnt:-1:{value}")
    kb.button(text="➕", callback_data=f"cnt:+1:{value}")
    kb.button(text="🔄 Сброс", callback_data=f"cnt:reset:0")
    kb.button(text="⬅️ Назад", callback_data=f"cnt:back:0")
    kb.adjust(2, 2)
    return kb


@router.message(Command("counter"))
async def cmd_counter(m: Message):
    start = 0
    await m.answer(f"Счётчик: {start}", reply_markup=counter_kb(start).as_markup())


@router.callback_query(F.data.startswith("cnt:"))
async def cb_counter(cq: CallbackQuery):
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
        await cq.message.edit_text("Главное меню:", reply_markup=main_menu_kb().as_markup())
        return

    await cq.message.edit_text(f"Счётчик: {value}", reply_markup=counter_kb(value).as_markup())


# ----- Админ-команды -----
@router.message(Command("users"))
async def cmd_users(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("Команда только для админа.")
        return
    await m.answer(f"Пользователей в базе: {count_users()}")


@router.message(Command("broadcast"))
async def cmd_broadcast(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("Команда только для админа.")
        return

    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Использование: /broadcast текст")
        return

    text = parts[1]
    user_ids = get_all_users_ids()
    ok, fail = 0, 0
    for uid in user_ids:
        try:
            await m.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1
            await asyncio.sleep(0)  # не блокируем цикл
    await m.answer(f"Рассылка завершена. Успех: {ok}, ошибок: {fail}.")


@router.message(Command("feedback"))
async def cmd_feedback(m: Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Напиши: /feedback твой текст")
        return

    if not ADMIN_ID:
        await m.answer("Админ не настроен.")
        return

    u = m.from_user
    prefix = f"Feedback от @{u.username or 'no_username'} (id={u.id}):\n"
    try:
        await m.bot.send_message(int(ADMIN_ID), prefix + parts[1])
        await m.answer("Отправлено ✅")
    except Exception:
        await m.answer("Не удалось отправить админу 😕")


# ===== HTTP-сервер для Render (keep-alive) =====
def start_http_server():
    port = int(os.environ.get("PORT", 8080))

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            pass  # тише в логах

    with TCPServer(("", port), Handler) as httpd:
        log.info(f"HTTP server on 0.0.0.0:{port}")
        httpd.serve_forever()


# ===== Запуск =====
async def run_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is not set")

    init_db()

    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token)

    log.info("Start polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # HTTP в фоне (для Render Free)
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(run_bot())
