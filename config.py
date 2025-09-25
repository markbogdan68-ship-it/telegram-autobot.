from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    admin_ids: tuple[int, ...] = tuple(
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    )
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    tz: str = os.getenv("TZ", "Europe/Berlin")

    # webhook
    webhook_url: str | None = os.getenv("WEBHOOK_URL") or None
    webhook_secret: str | None = os.getenv("WEBHOOK_SECRET") or None
    port: int = int(os.getenv("PORT", "8080"))

settings = Settings()
