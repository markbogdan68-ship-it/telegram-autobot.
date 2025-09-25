from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from  models import User

router = Router()

@router.message(F.text == "/start")
async def start(m: Message, session: AsyncSession):
    u = await session.get(User, m.from_user.id)
    if not u:
        u = User(id=m.from_user.id, username=m.from_user.username)
        session.add(u)
        await session.commit()
    await m.answer(
        "привет! я автономный бот-напоминалка.\n"
        "• /remind <через Nмин|в HH:MM|YYYY-MM-DD HH:MM> текст — создать\n"
        "• /list — список напоминаний\n"
        "• /help — помощь"
    )

@router.message(F.text == "/help")
async def help_(m: Message):
    await m.answer(
        "команды:\n"
        "• /remind 10мин позвонить маме\n"
        "• /remind 18:30 вынести мусор\n"
        "• /remind 2025-10-01 09:00 подать отчёт\n"
        "• /list — показать активные"
    )
