# db.py
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import Base, User  # важно: импортируем и Base, и User

# SQLite-файл лежит рядом с кодом
DATABASE_URL = "sqlite:///./db.sqlite3"

# движок (для SQLite включаем check_same_thread=False)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Создать таблицы, если их ещё нет."""
    Base.metadata.create_all(bind=engine)


def add_user(tg_id: int) -> None:
    """Добавить пользователя, если его ещё нет."""
    with SessionLocal() as session:
        exists = session.query(User).filter(User.tg_id == tg_id).first()
        if not exists:
            session.add(User(tg_id=tg_id))
            session.commit()


def count_users() -> int:
    """Вернуть количество пользователей в таблице users."""
    with SessionLocal() as session:
        return session.query(User).count()


def get_sample_users(limit: int = 10):
    """Вернуть несколько пользователей для примера/тестов."""
    with SessionLocal() as session:
        rows = session.query(User).order_by(User.id.desc()).limit(limit).all()
        return rows


def all_user_ids():
    """Вернуть список всех tg_id (для рассылок)."""
    with SessionLocal() as session:
        return [u.tg_id for u in session.query(User.tg_id).all()]
