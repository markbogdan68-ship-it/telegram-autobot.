# === imports (добавь, если их нет) ===
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# если у тебя РАНЕЕ не было router — раскомментируй следующую строку:
router = Router()


# =========================
# 1) Меню с несколькими кнопками
# =========================

def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️ Информация", callback_data="menu:info")
    kb.button(text="✉️ Связаться", url="https://t.me/your_username")  # <-- поменяй на свой @username
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(2, 1)  # 2 кнопки в первом ряду, 1 во втором
    return kb

@router.message(Command("menu"))
async def show_menu(m: Message):
    await m.answer(
        "Главное меню:",
        reply_markup=main_menu_kb().as_markup()
    )

@router.callback_query(F.data == "menu:info")
async def menu_info(cq: CallbackQuery):
    await cq.answer()  # закрыть "часики"
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


# ==========================================
# 2) Пример с кнопками и callback-ответами
#    (динамический счётчик: +1 / -1 / Сброс)
# ==========================================

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
    await m.answer(
        f"Счётчик: {start}",
        reply_markup=counter_kb(start).as_markup()
    )

@router.callback_query(F.data.startswith("cnt:"))
async def on_counter(cq: CallbackQuery):
    # форматы:
    # "cnt:-1:5"  -> действие, текущее значение
    # "cnt:+1:5"
    # "cnt:reset:0"
    # "cnt:back:0"
    try:
        _, action, raw = cq.data.split(":")
        value = int(raw)
    except Exception:
        await cq.answer("Некорректные данные", show_alert=True)
        return

    if action == "+1":
        value += 1
        await cq.answer("Плюс один ✅")
        await cq.message.edit_text(
            f"Счётчик: {value}",
            reply_markup=counter_kb(value).as_markup()
        )
    elif action == "-1":
        value -= 1
        await cq.answer("Минус один ✅")
        await cq.message.edit_text(
            f"Счётчик: {value}",
            reply_markup=counter_kb(value).as_markup()
        )
    elif action == "reset":
        value = 0
        await cq.answer("Сброшено")
        await cq.message.edit_text(
            f"Счётчик: {value}",
            reply_markup=counter_kb(value).as_markup()
        )
    elif action == "back":
        # возврат в главное меню из счётчика
        await cq.answer()
        await cq.message.edit_text(
            "Главное меню:",
            reply_markup=main_menu_kb().as_markup()
        )
