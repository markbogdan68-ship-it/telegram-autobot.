from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .models import Reminder
from .config import settings

def setup_scheduler(bot: Bot, session_factory):
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.tz))

    async def tick():
        async with session_factory() as session:  # type: AsyncSession
            now = datetime.now(timezone.utc)
            q = select(Reminder).where(Reminder.sent == False, Reminder.due_at <= now)  # noqa: E712
            rows = (await session.execute(q)).scalars().all()
            for r in rows:
                try:
                    await bot.send_message(r.user_id, f"🔔 Напоминание: {r.text}")
                    r.sent = True
                except Exception as e:
                    print("send error:", e)
            if rows:
                await session.commit()

    scheduler.add_job(tick, IntervalTrigger(seconds=60), id="reminders_tick", max_instances=1, coalesce=True)
    scheduler.start()
    return scheduler
