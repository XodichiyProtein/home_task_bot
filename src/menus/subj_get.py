from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.table_data import Subject


def get_subj_menu():
    output_message = "Выберите предмет:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for subj in Subject.__members__.keys():
        print(subj)
        button = InlineKeyboardButton(text=subj, callback_data=f"subj_{subj}")
        keyboard.inline_keyboard.append([button])

    return output_message, keyboard
