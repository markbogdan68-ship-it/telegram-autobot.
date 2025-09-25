import asyncio
import logging
import contextlib

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import web

from .config import settings
from .db import init_db, SessionLocal
from .scheduler import setup_scheduler
from .handlers import base as base_handlers
from .handlers import reminders as reminders_handlers
from .webhook import build_app

logging.basicConfig(level=logging.INFO)

async def session_middleware(handler, event, data):
    async with SessionLocal() as session:  # type: AsyncSession
        data["session"] = session
        try:
            result = await handler(event, data)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise

async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="начать"),
        BotCommand(command="help", description="помощь"),
        BotCommand(command="list", description="мои напоминания"),
        BotCommand(command="remind", description="создать напоминание"),
    ])

async def _bootstrap():
    await init_db()
    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware.register(session_middleware)
    dp.include_router(base_handlers.router)
    dp.include_router(reminders_handlers.router)
    await set_commands(bot)
    scheduler = setup_scheduler(bot, SessionLocal)
    return bot, dp, scheduler

async def main():
    bot, dp, scheduler = await _bootstrap()

    try:
        if settings.webhook_url:
            logging.info(f"Starting webhook server on 0.0.0.0:{settings.port}")
            app = build_app(bot, dp)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", settings.port)
            await site.start()
            while True:
                await asyncio.sleep(3600)
        else:
            logging.info("Starting in long-polling mode")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        with contextlib.suppress(Exception):
            scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
