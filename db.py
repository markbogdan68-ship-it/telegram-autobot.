from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# База данных SQLite (лежит в корне проекта)
DATABASE_URL = "sqlite:///./db.sqlite3"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # нужно для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -------------------------
# Модель пользователя
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)      # ID в базе
    tg_id = Column(Integer, unique=True, index=True)        # Telegram ID
    username = Column(String, nullable=True)                # @username
    is_admin = Column(Boolean, default=False)               # админ или нет

# -------------------------
# Инициализация базы
# -------------------------
def init_db():
    Base.metadata.create_all(bind=engine)

# -------------------------
# Добавление пользователя
# -------------------------
def add_user(tg_id: int, username: str = None) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            user = User(tg_id=tg_id, username=username)
            db.add(user)
            db.commit()
    finally:
        db.close()

# -------------------------
# Проверка админа
# -------------------------
def is_admin(tg_id: int) -> bool:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(tg_id=tg_id).first()
        return bool(user and user.is_admin)
    finally:
        db.close()

# -------------------------
# Список пользователей
# -------------------------
def get_all_users():
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()
