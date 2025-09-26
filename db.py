from typing import List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import Base, User

# Локальная БД-файлик рядом с кодом
DATABASE_URL = "sqlite:///./db.sqlite3"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # нужно для sqlite в одном процессе
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Создаём таблицы, если их ещё нет"""
    Base.metadata.create_all(bind=engine)


def add_user(tg_id: int, username: Optional[str] = None) -> None:
    """Сохраняем пользователя, если его ещё нет"""
    with SessionLocal() as s:
        exists = s.query(User).filter_by(tg_id=tg_id).first()
        if not exists:
            u = User(tg_id=tg_id, username=(username or "")[:100])
            s.add(u)
            s.commit()


def count_users() -> int:
    with SessionLocal() as s:
        return s.query(User).count()


def get_all_users_ids() -> List[int]:
    """Список tg_id всех пользователей"""
    with SessionLocal() as s:
        rows = s.query(User.tg_id).all()  # [(123,), (456,), ...]
        return [r[0] for r in rows]
