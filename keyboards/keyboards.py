from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CLASS_PREFIX, FB_PREFIX, ANN_PREFIX, DEV_PREFIX, BACK_PREFIX, MENU_PREFIX, LETTER_PREFIX, EDIT_HOMEWORK_PREFIX

from datetime import datetime, timedelta
from typing import Optional, Dict, List

def announcements_menu_kb(announcements_list: List[Dict]) -> types.InlineKeyboardMarkup:
    """
    Создает клавиатуру для меню объявлений, используя ПЕРЕДАННЫЙ список.

    :param announcements_list: Актуальный список объявлений.
    """
    builder = InlineKeyboardBuilder()
    
    if not announcements_list:
        builder.button(text="Нет актуальных объявлений 😔", callback_data=f"{ANN_PREFIX}no_ann")
    else:
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
    
    builder.button(text="➡️ Пропустить", callback_data=f"{FB_PREFIX}skip:{complaint_id}") 
    builder.button(text="💬 Ответить", callback_data=f"{FB_PREFIX}reply:{complaint_id}")
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

    if is_developer:
        builder.button(text="💻 Меню Разработчика", callback_data=f"{MENU_PREFIX}dev")
        builder.adjust(2, 5, 1)
    else:
        builder.adjust(2, 5)

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
