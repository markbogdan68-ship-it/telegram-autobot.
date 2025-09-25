from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

from ..models import Reminder
from ..config import settings

router = Router()

REL_RE = re.compile(r"(?i)^\s*/remind\s+(\d+)\s*(мин|минут|minute|minutes|m)\s+(.+)$")
AT_RE  = re.compile(r"(?i)^\s*/remind\s+(\d{1,2}):(\d{2})\s+(.+)$")
ABS_RE = re.compile(r"(?i)^\s*/remind\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})\s+(.+)$")

def to_utc(dt_local: datetime) -> datetime:
    return dt_local.astimezone(ZoneInfo("UTC"))

@router.message(lambda m: m.text and m.text.lower().startswith("/remind"))
async def add_reminder(m: Message, session: AsyncSession):
    text = m.text.strip()

    now_local = datetime.now(ZoneInfo(settings.tz))

    if (match := REL_RE.match(text)):
        mins = int(match.group(1))
        body = match.group(3)
        due_local = now_local + timedelta(minutes=mins)
    elif (match := AT_RE.match(text)):
        hh, mm = int(match.group(1)), int(match.group(2))
        body = match.group(3)
        due_local = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if due_local <= now_local:
            due_local += timedelta(days=1)
    elif (match := ABS_RE.match(text)):
        date_str, hh, mm, body = match.groups()
        y, mo, d = (int(x) for x in date_str.split("-"))
        due_local = datetime(y, mo, d, int(hh), int(mm), tzinfo=ZoneInfo(settings.tz))
    else:
        return await m.answer("не понял формат. примеры:\n/remind 15мин чай\n/remind 18:30 спорт\n/remind 2025-10-01 09:00 отчёт")

    due_utc = to_utc(due_local)

    r = Reminder(user_id=m.from_user.id, text=body, due_at=due_utc)
    session.add(r)
    await session.commit()

    await m.answer(f"ок! напомню {due_local.strftime('%Y-%m-%d %H:%M %Z')}: “{body}”. ✅")

@router.message(lambda m: m.text and m.text.strip() == "/list")
async def list_reminders(m: Message, session: AsyncSession):
    from sqlalchemy import select
    q = select(Reminder).where(Reminder.user_id == m.from_user.id, Reminder.sent == False).order_by(Reminder.due_at.asc())  # noqa
    rows = (await session.execute(q)).scalars().all()
    if not rows:
        return await m.answer("активных напоминаний нет.")
    lines = []
    for r in rows:
        local = r.due_at.astimezone(ZoneInfo(settings.tz))
        lines.append(f"• {local.strftime('%Y-%m-%d %H:%M %Z')} — {r.text} (#{r.id})")
    await m.answer("твои напоминания:\n" + "\n".join(lines))
