import logging
from aiogram import types, Router
from aiogram.types.input_file import FSInputFile
from src.handlers import allow_user
from src.menus.hw_get import get_hw_menu
from src.menus.subj_get import get_subj_menu
from src.menus.day_get import get_day_menu
from src.menus.base import get_base_menu
from src.table_data import Day, Subject
from src.config import bot
import src.config as conf
import src.state as st

logger = logging.getLogger(__name__)
dp = Router()


async def delete(call):
    await bot.delete_message(
        chat_id=call.message.chat.id, message_id=call.message.message_id
    )


# Обработчик нажатий на кнопки
@dp.callback_query()
async def handle_category_callback(callback: types.CallbackQuery):
    """
    Обработка callback от кнопок
    """
    if allow_user(callback):
        data = callback.data
        if data:
            if callback.message:
                if "main_menu_" in data:
                    button_id = None
                    try:
                        button_id = int(data.replace("main_menu_", ""))
                    except (ValueError, RuntimeError) as e:
                        logger.error("Не получилось получить button_id: %s", e)

                    if button_id == 1:
                        st.day = None
                        st.subject = None
                        st.hw = None
                        await delete(callback)
                        text, keyboard = get_subj_menu()

                        await callback.message.answer(
                            text=text,
                            reply_markup=keyboard,
                        )

                    elif button_id == 2:
                        st.day = None
                        st.subject = None
                        st.hw = None
                        st.remove = True
                        await delete(callback)
                        text, keyboard = get_subj_menu()

                        await callback.message.answer(
                            text=text,
                            reply_markup=keyboard,
                        )

                if "subj_" in data:
                    await delete(callback)

                    key = data.replace("subj_", "")
                    subject = Subject.__members__[key]
                    st.subject = subject

                    text, keyboard = get_day_menu()

                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                    )
                    print(data)

                if "day_" in data:
                    await delete(callback)
                    key = data.replace("day_", "")
                    day = Day.__members__[key]
                    st.day = day
                    if st.remove:
                        if conf.manager and st.subject:
                            if not conf.manager.clear_homework(st.subject, st.day):
                                logger.error("Не удалось удалить дз(")
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
                                    reply_markup=keyboard,  # клавиатура опционально
                                )
                            else:
                                await callback.message.answer(
                                    text, reply_markup=keyboard
                                )

                    else:
                        text = get_hw_menu()

                        await callback.message.answer(text=text)
                        print(data)
