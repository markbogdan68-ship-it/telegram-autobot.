# handlers.py
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def start(m: types.Message):
    await m.answer("Я запущен на Render ✅\nДоступные команды: /help, /ping")

@router.message(Command("help"))
async def help_cmd(m: types.Message):
    await m.answer("Команды:\n• /ping — проверка\n• /help — эта справка")

@router.message(Command("ping"))
async def ping(m: types.Message):
    await m.answer("pong 🏓")

# Ответ на любые другие сообщения
@router.message()
async def echo(m: types.Message):
    if m.text:
        await m.answer(f"Вы написали: {m.text}")
