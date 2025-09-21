from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Tuple

import src.config as conf

def get_class_select_menu() -> Tuple[str, InlineKeyboardMarkup]:
    """
    Возвращает текст и клавиатуру для выбора класса (число).
    """
    text = "Привет! 👋 Прежде чем начать, выбери свой класс (число):"
    
    buttons = []
    for class_num in sorted(conf.CLASS_CONFIG.keys()):
        buttons.append(
            InlineKeyboardButton(
                text=str(class_num), callback_data=f"select_class_{class_num}"
            )
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons[i:i + 3] for i in range(0, len(buttons), 3)
    ])
    
    return text, keyboard