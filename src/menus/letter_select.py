from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Tuple, List

import src.config as conf

def get_letter_select_menu(class_num: int) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Возвращает текст и клавиатуру для выбора буквы класса.
    """
    
    letters: List[str] = conf.CLASS_CONFIG.get(class_num, [])
    
    if not letters:
        text = f"Ошибка: для {class_num}-го класса нет доступных букв."
        return text, InlineKeyboardMarkup(inline_keyboard=[])
        
    text = f"Ты выбрал {class_num} класс. Теперь выбери букву:"
    
    buttons = []
    for letter in letters:
        class_name = f"{class_num}{letter}"
        buttons.append(
            InlineKeyboardButton(
                text=letter, callback_data=f"set_class_{class_name}"
            )
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    
    return text, keyboard