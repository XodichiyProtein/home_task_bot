from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.table_data import Day


def get_day_menu():
    output_message = "Выберите день:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for day in Day.__members__.keys():
        print(day)
        button = InlineKeyboardButton(text=day, callback_data=f"day_{day}")
        keyboard.inline_keyboard.append([button])

    # Добавление кнопки "Назад"
    back_button = InlineKeyboardButton(text="Назад", callback_data="back_to_subj_select")
    keyboard.inline_keyboard.append([back_button])

    return output_message, keyboard