from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Префиксы для CallbackData
CLASS_PREFIX = "select_class_"
LETTER_PREFIX = "select_letter_"
MENU_PREFIX = "menu_"
DEV_PREFIX = "dev_"
EDIT_HOMEWORK_PREFIX = "edit_hw_"
BACK_PREFIX = "back_"


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
    # builder.button(text="📚 Объявление", callback_data=f"{MENU_PREFIX}announcement")
    # builder.button(text="😎 В разработке", callback_data=f"{MENU_PREFIX}test")
    # builder.button(text="☎️ Связь", callback_data=f"{MENU_PREFIX}connection")

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
        builder.adjust(5, 1)
    else:
        builder.adjust(5)

    return builder.as_markup()


def get_developer_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру меню разработчика."""
    builder = InlineKeyboardBuilder()

    builder.button(text="🔄 Добавить таблицу", callback_data=f"{DEV_PREFIX}TableAdd")
    builder.button(text="👥 Добавить админа", callback_data=f"{DEV_PREFIX}AdminAdd")
    builder.button(text="👥 Удалить админа", callback_data=f"{DEV_PREFIX}AdminRemove")
    builder.button(text="❌ Закрыть меню", callback_data=f"{DEV_PREFIX}close")

    builder.adjust(3, 1)
    return builder.as_markup()
