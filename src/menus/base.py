from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
import src.config as conf
from typing import Optional, Tuple, Any, List

# Изменил сигнатуру функции, добавив user_id
def get_base_menu(user_id: int) -> Optional[Tuple[str, InlineKeyboardMarkup, Optional[str]]]:
    """
    Получение изображения таблицы, создание кнопок и текста главного меню
    """
    image: Optional[str] = None
    output_message = "🏠 Homeworks"

    if conf.manager:
        dir_path = Path(__file__).parent.parent.parent / "images"
        # Убедимся, что директория существует
        dir_path.mkdir(parents=True, exist_ok=True) 
        
        # Генерируем уникальное имя файла для предотвращения кэширования старой картинки
        import time
        timestamp = int(time.time())
        path = dir_path / f"hw_table_{conf.manager.class_name}_{timestamp}.png"
        
        # Получаем путь к изображению
        image = conf.manager.table_to_image(str(path))
        
        # Если изображение не сгенерировано (например, ошибка), image будет None
        photo_path = str(path) if image else None
        
    else:
        # Если менеджер не установлен, возвращаем только сообщение о необходимости выбрать класс
        return None

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    add_hw_button = InlineKeyboardButton(
        text="Добавить дз", callback_data="main_menu_1"
    )
    remove_hw_button = InlineKeyboardButton(
        text="Удалить дз", callback_data="main_menu_2"
    )
    
    refresh_button = InlineKeyboardButton(
        text="🔄 Обновить расписание", callback_data="main_menu_3"
    )
    
    keyboard.inline_keyboard.append([add_hw_button, remove_hw_button])
    keyboard.inline_keyboard.append([refresh_button])
    
    # НОВЫЙ БЛОК: Кнопка "Изменить класс" только для избранных
    if user_id in conf.PRIVILEGED_USERS:
        change_class_button = InlineKeyboardButton(
            text="✏️ Изменить класс", callback_data="main_menu_4" # Новое callback_data
        )
        keyboard.inline_keyboard.append([change_class_button])


    return output_message, keyboard, photo_path