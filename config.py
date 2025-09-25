from typing import Dict, List
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("BOT_TOKEN")
try:
    DEV_IDS_STR = os.getenv("DEVELOPER_IDS", "")
    DEVELOPER_IDS: List[int] = list(map(int, filter(None, DEV_IDS_STR.split(","))))
except ValueError:
    print("Ошибка при чтении DEVELOPER_IDS из .env. Проверьте формат.")
    DEVELOPER_IDS: List[int] = []

CLASS_CONFIG: Dict[int, List[str]] = {
    5: ["А", "Б"],
    6: ["А", "Б"],
    7: ["А", "Б", "В"],
    8: ["А", "Б", "В"],
    9: ["А", "Б", "В"],
    10: ["А", "Б"],
    11: ["А", "Б"],
}

# --- НОВЫЕ КОНСТАНТЫ ---
DOWNLOAD_DIR = "downloads/"

CLASS_PREFIX = "select_class_"
LETTER_PREFIX = "select_letter_"
MENU_PREFIX = "menu_"
DEV_PREFIX = "dev_"
EDIT_HOMEWORK_PREFIX = "edit_hw_"

import logging
import sys

# --- 1. Форматы ---
# Кастомный формат для логов активности пользователя
CUSTOM_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - UserID:%(user_id)s - Action:%(action)s - Handler:%(handler)s - %(message)s"
# Стандартный формат для системных логов (aiogram, asyncio и т.д.)
STANDARD_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"


# --- 2. Кастомный Адаптер Логгера ---
class CustomLoggerAdapter(logging.LoggerAdapter):
    """
    Адаптер, который безопасно добавляет поля 'user_id', 'action', 'handler' к лог-записи,
    подставляя 'N/A', если поля отсутствуют. Это предотвращает ошибки KeyError.
    """

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})

        # Безопасно получаем значения, подставляя 'N/A' при отсутствии
        extra.update(
            {
                "user_id": extra.get("user_id", "N/A"),
                "action": extra.get("action", "N/A"),
                "handler": extra.get("handler", "N/A"),
            }
        )

        return msg, kwargs


# --- 3. Функция настройки логирования ---
def setup_logging():
    """
    Централизованная функция настройки логирования.
    Создает два отдельных файла для системных логов и логов активности.
    """
    # Создаем форматтеры
    standard_formatter = logging.Formatter(STANDARD_LOG_FORMAT)
    custom_formatter = logging.Formatter(CUSTOM_LOG_FORMAT)

    # 3.1. Настройка корневого логгера (для aiogram/системных логов)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Очищаем обработчики, чтобы избежать дублирования
    root_logger.handlers.clear()

    # Обработчик для системных логов в файл 'system_bot.log'
    system_file_handler = logging.FileHandler(
        "system_bot.log", mode="a", encoding="utf-8"
    )
    system_file_handler.setFormatter(standard_formatter)
    system_file_handler.setLevel(logging.INFO)
    root_logger.addHandler(system_file_handler)

    # Консольный обработчик для системных логов
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)

    # 3.2. Настройка кастомного логгера (для активности пользователя)
    bot_base_logger = logging.getLogger("bot_logger")
    bot_base_logger.setLevel(logging.INFO)
    # Ключевой шаг: Отключаем распространение логов в root_logger
    bot_base_logger.propagate = False

    # Обработчик для файла 'user_activity.log' с кастомным форматом
    custom_file_handler = logging.FileHandler(
        "user_activity.log", mode="a", encoding="utf-8"
    )
    custom_file_handler.setFormatter(custom_formatter)

    bot_base_logger.handlers.clear()
    bot_base_logger.addHandler(custom_file_handler)

    # 4. Возвращаем адаптированный логгер для использования в коде
    return CustomLoggerAdapter(bot_base_logger, {})


# Глобальный объект для импорта: запустит настройку при импорте
bot_logger = setup_logging()
