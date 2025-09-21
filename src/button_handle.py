# src/button_handle.py

import logging
from aiogram import types, Router
from aiogram.types.input_file import FSInputFile
from src.menus.hw_get import get_hw_menu
from src.menus.subj_get import get_subj_menu
from src.menus.day_get import get_day_menu
from src.menus.base import get_base_menu
from src.menus.letter_select import get_letter_select_menu
from src.table_data import Day, Subject
from src.config import bot
import src.config as conf
import src.state as st
from src.file_data import get_table_from_file
from src.table_data import HomeworkDataFrame

logger = logging.getLogger(__name__)
dp = Router()


async def delete(call):
    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=call.message.message_id
    )


# Обработчик нажатий на кнопки
@dp.callback_query()
async def handle_category_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "N/A"
    data = callback.data
    
    log_extra = {'user_id': user_id, 'username': username}
    
    if data and callback.message:
        
        # Новый блок: Выбор класса (число)
        if "select_class_" in data:
            logging.info("Пользователь %d выбрал число класса.", user_id, extra=log_extra)
            await delete(callback)
            try:
                class_num = int(data.replace("select_class_", ""))
                text, keyboard = get_letter_select_menu(class_num)

                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard,
                )
            except ValueError as e:
                logging.error("Ошибка при парсинге числа класса для пользователя %d: %s", user_id, e, extra=log_extra)

        # Новый блок: Установка класса (буква)
        elif "set_class_" in data:
            await delete(callback)
            class_name = data.replace("set_class_", "")
            conf.set_user_class(user_id, class_name)
            logging.info("Пользователь %d выбрал класс %s", user_id, class_name, extra=log_extra)
            
            # Инициализация менеджера ДЗ для нового класса
            try:
                pd_table = get_table_from_file(class_name)
                conf.set_manager(HomeworkDataFrame(pd_table, class_name))
                logging.info("Менеджер ДЗ инициализирован для класса: %s", class_name, extra=log_extra)
            except Exception as e:
                logging.error("Ошибка инициализации менеджера для класса %s: %s", class_name, e, extra=log_extra)
                await callback.message.answer("Произошла ошибка при загрузке данных вашего класса. Попробуйте позже.")
                return

            menu = get_base_menu()
            if menu:
                text, keyboard, photo_path = menu
                if photo_path:
                    await callback.message.answer_photo(
                        photo=FSInputFile(photo_path),
                        caption=text,
                        reply_markup=keyboard,
                    )
                else:
                    await callback.message.answer(text, reply_markup=keyboard)

        # Основная логика (работает только после выбора класса)
        elif conf.manager and conf.get_user_class(user_id):
            if "main_menu_" in data:
                button_id = None
                try:
                    button_id = int(data.replace("main_menu_", ""))
                    logging.info("Пользователь %d нажал на кнопку %d", user_id, button_id, extra=log_extra)
                except (ValueError, RuntimeError) as e:
                    logging.error("Не получилось получить button_id для пользователя %d: %s", user_id, e, extra=log_extra)

                if button_id == 1:
                    await delete(callback)
                    menu = get_subj_menu()
                    if menu:
                        await callback.message.answer(text=menu[0], reply_markup=menu[1])

                elif button_id == 2:
                    await delete(callback)
                    st.remove = True
                    menu = get_subj_menu()
                    if menu:
                        await callback.message.answer(text=menu[0], reply_markup=menu[1])

            elif "subj_" in data:
                await delete(callback)
                key = data.replace("subj_", "")
                subject = Subject.__members__[key]
                st.subject = subject
                logging.info("Пользователь %d выбрал предмет %s", user_id, subject.value, extra=log_extra)

                menu = get_day_menu()
                if menu:
                    await callback.message.answer(text=menu[0], reply_markup=menu[1])

            elif "day_" in data:
                await delete(callback)
                key = data.replace("day_", "")
                day = Day.__members__[key]
                st.day = day
                logging.info("Пользователь %d выбрал день недели %s", user_id, day.value, extra=log_extra)

                if st.remove:
                    if conf.manager and st.subject:
                        if not conf.manager.clear_homework(st.subject, st.day):
                            logging.error("Не удалось удалить дз для пользователя %d", user_id, extra=log_extra)
                        else:
                            logging.info("Пользователь %d удалил ДЗ для %s %s", user_id, st.subject.value, st.day.value, extra=log_extra)
                        
                        st.day = None
                        st.subject = None
                        st.hw = None
                        st.remove = False
                    
                    menu = get_base_menu()
                    if menu:
                        text, keyboard, photo_path = menu
                        if photo_path:
                            await callback.message.answer_photo(
                                photo=FSInputFile(photo_path),
                                caption=text,
                                reply_markup=keyboard,
                            )
                        else:
                            await callback.message.answer(
                                text, reply_markup=keyboard
                            )

                else:
                    text = get_hw_menu()
                    await callback.message.answer(text=text)