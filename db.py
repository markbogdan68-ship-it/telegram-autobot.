# db.py
from datetime import datetime
import os

from sqlalchemy import create_engine, Column, Integer, BigInteger, DateTime, select
from sqlalchemy.orm import declarative_base, Session

# По умолчанию SQLite-файл рядом с кодом (переживает перезапуск, но теряется при новом деплое).
# Позже можем подключить внешнюю БД (например, Neon/Postgres), тогда положим URL в DATABASE_URL.
DB_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

engine = create_engine(DB_URL, echo=False, future=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)        # внутренний id
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    """Создать таблицы, если их ещё нет."""
    Base.metadata.create_all(engine)


def add_user(tg_id: int) -> None:
    """Сохранить пользователя, если его ещё нет."""
    with Session(engine) as s:
        exists = s.scalar(select(User).where(User.tg_id == tg_id))
        if not exists:
            s.add(User(tg_id=tg_id))
            s.commit()


def count_users() -> int:
    with Session(engine) as s:
        return s.query(User).count()


def get_sample_users(limit: int = 10) -> list[int]:
    with Session(engine) as s:
        return s.execute(
            select(User.tg_id).order_by(User.created_at.desc()).limit(limit)
        ).scalars().all()


def all_user_ids() -> list[int]:
    with Session(engine) as s:
        return s.execute(select(User.tg_id)).scalars().all()
