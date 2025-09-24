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
