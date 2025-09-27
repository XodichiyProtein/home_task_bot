from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
import json

# Префиксы для CallbackData
CLASS_PREFIX = "select_class_"
LETTER_PREFIX = "select_letter_"
MENU_PREFIX = "menu_"
DEV_PREFIX = "dev_"
EDIT_HOMEWORK_PREFIX = "edit_hw_"
BACK_PREFIX = "back_"
ANN_PREFIX = "ann_" 
FB_PREFIX = "fb_"


COMPLAINTS_FILE = 'complaints.json'
COMPLAINTS_DATA = [] 
NEXT_COMPLAINT_ID = 1

ANNOUNCEMENTS_DATA = [] 
NEXT_ANNOUNCEMENT_ID = 1 
ANNOUNCEMENTS_FILE = 'announcements.json'



def load_complaints():
    """Загружает жалобы из локального JSON-файла."""
    global COMPLAINTS_DATA, NEXT_COMPLAINT_ID
    if os.path.exists(COMPLAINTS_FILE):
        try:
            with open(COMPLAINTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                COMPLAINTS_DATA = data.get('complaints', [])
                if COMPLAINTS_DATA:
                    max_id = max(c['id'] for c in COMPLAINTS_DATA)
                    NEXT_COMPLAINT_ID = max_id + 1
                else:
                    NEXT_COMPLAINT_ID = 1
        except (json.JSONDecodeError, FileNotFoundError):
            COMPLAINTS_DATA = []
            NEXT_COMPLAINT_ID = 1
    else:
        COMPLAINTS_DATA = []
        NEXT_COMPLAINT_ID = 1

def save_complaints():
    """Сохраняет жалобы в локальный JSON-файл."""
    data = {'complaints': COMPLAINTS_DATA}
    with open(COMPLAINTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_complaint_id() -> int:
    """Получает следующий ID для новой жалобы."""
    global NEXT_COMPLAINT_ID
    current_id = NEXT_COMPLAINT_ID
    NEXT_COMPLAINT_ID += 1
    return current_id

def load_announcements():
    """Загружает объявления из локального JSON-файла."""
    global ANNOUNCEMENTS_DATA, NEXT_ANNOUNCEMENT_ID
    if os.path.exists(ANNOUNCEMENTS_FILE):
        try:
            with open(ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ANNOUNCEMENTS_DATA = data.get('announcements', [])
                # Устанавливаем NEXT_ANNOUNCEMENT_ID
                if ANNOUNCEMENTS_DATA:
                    max_id = max(ann['id'] for ann in ANNOUNCEMENTS_DATA)
                    NEXT_ANNOUNCEMENT_ID = max_id + 1
                else:
                    NEXT_ANNOUNCEMENT_ID = 1
        except (json.JSONDecodeError, FileNotFoundError):
            # Если файл пуст или поврежден, начинаем с чистого листа
            ANNOUNCEMENTS_DATA = []
            NEXT_ANNOUNCEMENT_ID = 1
    else:
        ANNOUNCEMENTS_DATA = []
        NEXT_ANNOUNCEMENT_ID = 1

def save_announcements():
    """Сохраняет объявления в локальный JSON-файл."""
    data = {'announcements': ANNOUNCEMENTS_DATA}
    with open(ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_next_announcement_id() -> int:
    """Получает следующий ID для нового объявления (имитация DB)."""
    global NEXT_ANNOUNCEMENT_ID
    current_id = NEXT_ANNOUNCEMENT_ID
    NEXT_ANNOUNCEMENT_ID += 1
    return current_id

def announcements_menu_kb(announcements_list: List[Dict]) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру для меню объявлений, используя ПЕРЕДАННЫЙ список.

    :param announcements_list: Актуальный список объявлений.
    """
    builder = InlineKeyboardBuilder()
    
    if not announcements_list: # <-- Используем переданный список
        builder.button(text="Нет актуальных объявлений 😔", callback_data=f"{ANN_PREFIX}no_ann")
    else:
        # Создаем кнопки для всех объявлений
        for ann in announcements_list:
            title = ann.get('title', f"Объявление #{ann['id']}") 
            
            builder.button(
                text=f"📢 {title}", 
                callback_data=f"{ANN_PREFIX}view:{ann['id']}"
            )

    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{BACK_PREFIX}main-menu"))
    return builder.as_markup()

def announcement_detail_kb(announcement_id: int, is_developer: bool = False) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру для детального просмотра объявления, 
    включая кнопку удаления для разработчиков.
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для разработчиков: "Удалить объявление"
    if is_developer:
        builder.button(
            text="🗑️ Удалить объявление", 
            callback_data=f"{ANN_PREFIX}delete:{announcement_id}"
        )
        
    builder.button(
        text="⬅️ Назад", 
        callback_data=f"{BACK_PREFIX}ann-menu"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_edit_homework_keyboard(
    lesson_numbers: list, date_str: str
) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками для выбора номера урока.

    :param lesson_numbers: Список номеров уроков для отображения.
    :param date_str: Дата в формате 'YYYY-MM-DD'.
    """
    builder = InlineKeyboardBuilder()

    for number in lesson_numbers:
        builder.button(
            text=f"Урок {number}",
            callback_data=f"{EDIT_HOMEWORK_PREFIX}{date_str}:{number}",
        )

    builder.button(
        text="⬅️ Назад к расписанию",
        callback_data=f"{BACK_PREFIX}main-menu",
    )

    # 2. Корректируем расположение: 3 кнопки в ряду, затем 1 кнопка "Назад"
    builder.adjust(3, 1)
    return builder.as_markup()


def get_class_keyboard(
    class_config: Dict[int, List[str]],
) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для выбора класса (5-11)."""
    builder = InlineKeyboardBuilder()

    for class_num in class_config.keys():
        builder.button(
            text=f"{class_num} класс", callback_data=f"{CLASS_PREFIX}{class_num}"
        )

    builder.adjust(3)
    return builder.as_markup()


def get_letter_keyboard(
    class_num: int, class_config: Dict[int, List[str]]
) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для выбора буквы класса."""
    builder = InlineKeyboardBuilder()

    # Получаем список букв для выбранного класса
    letters = class_config.get(class_num, [])

    for letter in letters:
        builder.button(
            text=f"{class_num}{letter}",
            callback_data=f"{LETTER_PREFIX}{class_num}_{letter}",
        )

    builder.adjust(3, 3, 3)
    return builder.as_markup()

def get_complaint_keyboard(complaint_id: int) -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для обработки жалобы."""
    builder = InlineKeyboardBuilder()
    
    # fb_skip:<id>
    builder.button(text="➡️ Пропустить", callback_data=f"{FB_PREFIX}skip:{complaint_id}") 
    # fb_reply:<id>
    builder.button(text="💬 Ответить", callback_data=f"{FB_PREFIX}reply:{complaint_id}")
    # fb_ignore:<id>
    builder.button(text="🗑️ Игнорировать", callback_data=f"{FB_PREFIX}ignore:{complaint_id}")
    builder.button(text="❌ В меню", callback_data=f"{FB_PREFIX}back:{complaint_id}")
    
    builder.adjust(3, 1)
    return builder.as_markup()

def get_main_menu_keyboard(
    is_developer: bool = False, current_center_date: Optional[datetime] = None
) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру главного меню с динамическим отображением дат.

    :param is_developer: Флаг для отображения меню разработчика.
    :param current_center_date: Дата, которая будет отображена по центру.
    """
    builder = InlineKeyboardBuilder()

    if current_center_date is None:
        current_center_date = datetime.now()

    minus_1_day = current_center_date - timedelta(days=1)
    plus_1_day = current_center_date + timedelta(days=1)

    # Формат даты для отображения на кнопке
    display_format = "%d.%m"
    callback_format = "%Y-%m-%d"  # Формат для передачи в callback

    # Кнопки первого ряда
    builder.button(text="📚 Объявление", callback_data=f"{ANN_PREFIX}ViewMenu")
    # builder.button(text="😎 В разработке", callback_data=f"{MENU_PREFIX}test")
    builder.button(text="☎️ Связь", callback_data=f"{FB_PREFIX}connection")

    builder.button(
        text="<",
        callback_data=f"{MENU_PREFIX}scroll_left:{current_center_date.strftime(callback_format)}",
    )
    builder.button(
        text=minus_1_day.strftime(display_format),
        callback_data=f"{MENU_PREFIX}date:{minus_1_day.strftime(callback_format)}",
    )
    builder.button(
        text=current_center_date.strftime(display_format),
        callback_data=f"{MENU_PREFIX}date:{current_center_date.strftime(callback_format)}",
    )
    builder.button(
        text=plus_1_day.strftime(display_format),
        callback_data=f"{MENU_PREFIX}date:{plus_1_day.strftime(callback_format)}",
    )
    builder.button(
        text=">",
        callback_data=f"{MENU_PREFIX}scroll_right:{current_center_date.strftime(callback_format)}",
    )

    # Переставляем порядок, чтобы кнопки дат были во втором ряду
    if is_developer:
        builder.button(text="💻 Меню Разработчика", callback_data=f"{DEV_PREFIX}dev")
        # builder.adjust(3, 5, 1)
        builder.adjust(2, 5, 1)
    else:
        builder.adjust(5)

    return builder.as_markup()


def get_developer_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру меню разработчика."""
    builder = InlineKeyboardBuilder()

    builder.button(text="🔄 Добавить таблицу", callback_data=f"{DEV_PREFIX}TableAdd")
    builder.button(text='🔮 Жалобы', callback_data=f'{FB_PREFIX}complaints')
    builder.button(text="➕ Создать объявление", callback_data=f"{ANN_PREFIX}CreateStart")
    builder.button(text="👥 Добавить админа", callback_data=f"{DEV_PREFIX}AdminAdd")
    builder.button(text="👥 Удалить админа", callback_data=f"{DEV_PREFIX}AdminRemove")
    builder.button(text="❌ Закрыть меню", callback_data=f"{DEV_PREFIX}close")

    builder.adjust(3, 2, 1)
    return builder.as_markup()
load_announcements()
load_complaints() 