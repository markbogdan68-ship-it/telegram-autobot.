import os
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import add_user, get_all_users_ids, count_users

router = Router()

ADMIN_ID = os.getenv("ADMIN_ID")  # можно не задавать


# ---------- Меню (inline) ----------
def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Информация", callback_data="menu:info")
    kb.button(text="✉️ Связаться", url="https://t.me/your_username")  # замени на свой @username
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(2, 1)
    return kb


@router.message(CommandStart())
async def cmd_start(m: Message):
    add_user(m.from_user.id, m.from_user.username)
    await m.answer(
        "Я запущен на Render ✅\nДоступные команды: /help, /ping, /menu, /counter, /users, /broadcast, /feedback",
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(
        "Команды:\n"
        "• /ping — проверка\n"
        "• /menu — меню с кнопками\n"
        "• /counter — счётчик с inline-кнопками\n"
        "• /users — количество пользователей (только админ)\n"
        "• /broadcast <текст> — рассылка (только админ)\n"
        "• /feedback <текст> — написать админу"
    )


@router.message(Command("ping"))
async def cmd_ping(m: Message):
    await m.answer("pong 🏓")


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
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "menu:back")
async def menu_back(cq: CallbackQuery):
    await cq.answer("Возврат в меню")
    await cq.message.edit_text("Главное меню:", reply_markup=main_menu_kb().as_markup())


# ---------- Счётчик ----------
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


# ---------- Админ-команды ----------
def is_admin(user_id: int) -> bool:
    if not ADMIN_ID:
        return False
    try:
        return int(ADMIN_ID) == int(user_id)
    except Exception:
        return False


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
    await m.answer(f"Рассылка завершена. Успех: {ok}, ошибок: {fail}.")


@router.message(Command("feedback"))
async def cmd_feedback(m: Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Напиши: /feedback твой текст")
        return

    admin = ADMIN_ID
    if not admin:
        await m.answer("Админ не настроен.")
        return

    txt = parts[1]
    u = m.from_user
    prefix = f"Feedback от @{u.username or 'no_username'} (id={u.id}):\n"
    try:
        await m.bot.send_message(int(admin), prefix + txt)
        await m.answer("Отправлено ✅")
    except Exception:
        await m.answer("Не удалось отправить админу 😕")
