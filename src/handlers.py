import logging
from aiogram import types, Router
from aiogram.types.input_file import FSInputFile

from src.config import ALLOW_USER
import src.config as conf
from src.menus.base import get_base_menu
import src.state as st

logger = logging.getLogger(__name__)
dp = Router()


def allow_user(message: types.Message | types.CallbackQuery) -> bool:
    """
    Проверяет разрешенный ли пользователь, по chat.id либо по from_user.id
    """
    if message and message.from_user and message.from_user.id in ALLOW_USER:
        return True
    return False


@dp.message()
async def echo_message(message: types.Message):
    """
    Обработчик сообщений пользователя
    """
    if allow_user(message):
        if not st.remove and st.day and st.subject and st.hw is None:
            if conf.manager and message.text:
                if not conf.manager.set_homework(st.subject, st.day, message.text):
                    logger.error("Не удалось поставить дз")

                st.day = None
                st.subject = None
                st.hw = None

        menu = get_base_menu()
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
