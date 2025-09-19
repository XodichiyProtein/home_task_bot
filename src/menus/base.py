from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
import src.config as conf


def get_base_menu():
    """
    Получение изображения таблицы, создание кнопок и текста главного меню
    """
    image = None
    output_message = "🏠 Homeworks"

    if conf.manager:
        dir_path = Path(__file__).parent.parent.parent / "images"
        path = dir_path / f"{len([dir_path.iterdir()])}.png"
        image = conf.manager.table_to_image(str(path))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    add_hw_button = InlineKeyboardButton(
        text="Добавить дз", callback_data="main_menu_1"
    )
    remove_hw_button = InlineKeyboardButton(
        text="Удалить дз", callback_data="main_menu_2"
    )
    keyboard.inline_keyboard.append([add_hw_button, remove_hw_button])

    return output_message, keyboard, image
