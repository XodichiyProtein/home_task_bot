# src/handlers.py

import logging
from aiogram import types, Router
from aiogram.types.input_file import FSInputFile

import src.config as conf
from src.menus.base import get_base_menu
from src.menus.class_select import get_class_select_menu
import src.state as st
from src.file_data import get_table_from_file
from src.table_data import HomeworkDataFrame

logger = logging.getLogger(__name__)
dp = Router()


@dp.message()
async def echo_message(message: types.Message):
    """
    Обработчик сообщений пользователя
    """
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    # Добавляем user_id и username в контекст логгирования
    log_extra = {'user_id': user_id, 'username': username}
    
    class_name = conf.get_user_class(user_id)
    
    # Шаг 1: Проверка первого запуска (выбора класса)
    if not class_name:
        logging.info("Пользователь %d (username: %s) начал выбор класса.", user_id, username, extra=log_extra)
        text, keyboard = get_class_select_menu()
        await message.answer(text, reply_markup=keyboard)
        return
        
    # Шаг 2: Инициализация менеджера для пользователя
    if not conf.manager:
        try:
            pd_table = get_table_from_file(class_name)
            conf.set_manager(HomeworkDataFrame(pd_table, class_name))
            logging.info("Менеджер ДЗ инициализирован для класса: %s", class_name, extra=log_extra)
        except Exception as e:
            logging.error("Ошибка инициализации менеджера для класса %s: %s", class_name, e, extra=log_extra)
            await message.answer("Произошла ошибка при загрузке данных вашего класса. Попробуйте позже.")
            return

    # Шаг 3: Основная логика работы
    if not st.remove and st.day and st.subject and st.hw is None:
        if conf.manager and message.text:
            if not conf.manager.set_homework(st.subject, st.day, message.text):
                logging.error("Не удалось поставить дз для пользователя %d", user_id, extra=log_extra)
            else:
                logging.info("Пользователь %d добавил ДЗ для %s %s", user_id, st.subject.value, st.day.value, extra=log_extra)

            st.day = None
            st.subject = None
            st.hw = None

    menu = get_base_menu(user_id)
    if menu:
        text, keyboard, photo_path = menu
        if photo_path:
            await message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=text,
                reply_markup=keyboard,
            )
        else:
            await message.answer(text, reply_markup=keyboard)