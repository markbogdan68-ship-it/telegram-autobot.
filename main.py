# main.py (добавления сверху файла)
import os
import time
import logging
# ... остальное, что уже было импортировано

# --- ЛОГИРОВАНИЕ ---
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_level = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}.get(LEVEL, logging.INFO)

logging.basicConfig(
    level=_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")

START_TS = time.time()
