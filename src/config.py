# src/config.py

import logging
import sys
import os
from typing import TYPE_CHECKING, Optional, Dict, List
from dotenv import load_dotenv
from datetime import date
from pathlib import Path
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import json
import pandas as pd

if TYPE_CHECKING:
    from src.table_data import HomeworkDataFrame

# Директория для хранения таблиц классов
if os.name == "nt":
    TABLE_DIR = Path("./class_tables")
else:
    TABLE_DIR = Path("/run/media/chert/Job/Personal Notes/2. Области/Учеба/class_tables")

TABLE_DIR.mkdir(parents=True, exist_ok=True) # Создаем директорию, если ее нет

# Путь к файлу для сохранения данных пользователей
USERS_DATA_FILE = TABLE_DIR / "users_data.json"
# Путь к файлу для таблицы пользователей
USERS_TABLE_FILE = TABLE_DIR / "users_table.md"

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

manager: Optional["HomeworkDataFrame"]
manager = None

# Словарь для хранения информации о классе пользователя
# Key: user_id (int), Value: class_name (str, e.g., '10A')
user_classes: Dict[int, str] = {}

# Конфигурация классов
CLASS_CONFIG: Dict[int, List[str]] = {
    5: ["А", "Б", "В", "Г"],
    6: ["А", "Б", "В"],
    7: ["А", "Б", "В"],
    8: ["А", "Б"],
    9: ["А", "Б"],
    10: ["А"],
    11: ["Б"],
}

def load_user_classes():
    """Загрузка данных пользователей при запуске."""
    global user_classes
    if USERS_DATA_FILE.exists():
        with open(USERS_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Конвертируем ключи из str в int
            user_classes = {int(k): v for k, v in data.items()}

def save_user_classes():
    """Сохранение данных пользователей и обновление таблицы."""
    with open(USERS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_classes, f, ensure_ascii=False, indent=4)
    generate_users_table()

def generate_users_table():
    """Генерирует и сохраняет Markdown-таблицу со списком пользователей и их классов."""
    data = {'User ID': list(user_classes.keys()), 'Class': list(user_classes.values())}
    df = pd.DataFrame(data)
    with open(USERS_TABLE_FILE, "w", encoding="utf-8") as f:
        f.write(df.to_markdown(index=False))

load_user_classes()
generate_users_table()


if not BOT_TOKEN:  # Проверка токена
    print("Error: Please set BOT_TOKEN in your .env file.")
    sys.exit(1)


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

class CustomFormatter(logging.Formatter):
    """
    Класс для форматирования логов, который безопасно добавляет user_id,
    даже если его нет в записи.
    """
    def format(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        return super().format(record)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # формат: "21-08-25 19:40:12 [INFO] сообщение"
    formatter = CustomFormatter(
        fmt="%(asctime)s | [%(levelname)s] %(name)s | (user_id=%(user_id)s) | %(message)s",
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

    file_handler = logging.FileHandler(
        log_dir / f"bot_{date_string}.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def set_manager(manager_in: "HomeworkDataFrame"):
    global manager
    manager = manager_in


def get_user_class(user_id: int) -> Optional[str]:
    """Получает класс пользователя по его ID."""
    return user_classes.get(user_id)


def set_user_class(user_id: int, class_name: str) -> None:
    """Устанавливает класс для пользователя и сохраняет его."""
    user_classes[user_id] = class_name
    save_user_classes()

def clear_user_class(user_id: int) -> None:
    """Удаляет класс у пользователя, обнуляя его."""
    if user_id in user_classes:
        del user_classes[user_id]
        save_user_classes()
        logging.info("Класс пользователя был сброшен.", extra={'user_id': user_id})


def get_table_path_for_class(class_name: str) -> Path:
    """Генерирует путь к файлу таблицы для конкретного класса."""
    return TABLE_DIR / f"ДЗ_{class_name}.md"