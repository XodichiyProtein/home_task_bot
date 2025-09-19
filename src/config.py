import logging
import sys
import os
from typing import TYPE_CHECKING, Optional
from dotenv import load_dotenv
from datetime import date
from pathlib import Path
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

if TYPE_CHECKING:
    from src.table_data import HomeworkDataFrame

if os.name == "nt":
    FILE_PATH = Path("D:/DZ/ДЗ.md")
else:
    FILE_PATH = Path("/run/media/chert/Job/Personal Notes/2. Области/Учеба/ДЗ.md")

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
allow_user_id = os.getenv("ALLOW_USER")

manager: Optional["HomeworkDataFrame"]
manager = None

if not BOT_TOKEN or not allow_user_id:  # Проверка токена и разрешенного id на наличее
    print("Error: Please set BOT_TOKEN and ALLOW_USER in your .env file.")
    sys.exit(1)

try:
    ALLOW_USER = list(map(int, (allow_user_id).split(',')))
except ValueError:
    print("Error: The ALLOW_USER environment variable must be a valid integer.")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # формат: "21-08-25 19:40:12 [INFO] сообщение"
    formatter = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] %(name)s | %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )
    # вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # вывод в файл
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    date_string = today.strftime("%Y-%m-%d")
    log_file = log_dir / f"{date_string}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # добавляем хэндлеры
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def set_manager(manager_in: "HomeworkDataFrame"):
    global manager
    manager = manager_in
