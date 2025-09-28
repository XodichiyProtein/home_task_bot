from aiogram import types, Router, F
from aiogram.types import BufferedInputFile
from db.database import get_user_class, set_user_class

from config import (
    CLASS_CONFIG,
    CLASS_PREFIX,
    LETTER_PREFIX,
    MENU_PREFIX,
    
)
from .announcement.annoucement import ANNOUNCEMENTS_DATA
from keyboards.keyboards import (
    get_class_keyboard,
    get_letter_keyboard,
    get_main_menu_keyboard,
    get_developer_menu_keyboard,
    announcements_menu_kb,
    get_edit_homework_keyboard,
    BACK_PREFIX,
)
from utils.parser import create_schedule_image, get_lesson_numbers
from db.database import is_developer


from datetime import datetime, timedelta

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_class = get_user_class(user_id)
    is_dev = is_developer(user_id)

    if user_class:
        class_num, class_letter = user_class
        await message.answer(
            f"👋 С возвращением! Ваш класс **{class_num}{class_letter}** установлен.",
            reply_markup=get_main_menu_keyboard(is_developer=is_dev),
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "Добро пожаловать! Пожалуйста, выберите ваш класс (5-11).",
            reply_markup=get_class_keyboard(CLASS_CONFIG),
        )


@router.callback_query(F.data.startswith(f"{MENU_PREFIX}date:"))
async def callback_show_date_data(callback: types.CallbackQuery):
    await callback.answer()

    date_str = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    # Получаем класс пользователя из БД
    user_class = get_user_class(user_id)
    if not user_class:
        await callback.message.answer("Пожалуйста, сначала выберите ваш класс.")
        return

    class_num, class_letter = user_class

    # Получаем изображение расписания
    schedule_image_buffer = create_schedule_image(class_num, class_letter, date_str)
    numer_lesson = get_lesson_numbers(class_num, class_letter, date_str)
    if schedule_image_buffer is None:
        await callback.message.answer("Расписание на эту дату не найдено.")
        return

    # Отправляем изображение и клавиатуру для редактирования
    image = BufferedInputFile(schedule_image_buffer.getvalue(), filename="schedule.png")
    await callback.message.delete()  # Удаляем предыдущее сообщение с кнопками дат

    await callback.message.answer_photo(
        photo=image,
        caption="Ваше расписание. Выберите номер урока для изменения домашнего задания:",
        reply_markup=get_edit_homework_keyboard(numer_lesson, date_str),
    )


@router.callback_query(F.data.startswith(f"{MENU_PREFIX}scroll_right:"))
async def callback_scroll_right(callback: types.CallbackQuery):
    await callback.answer()
    current_date_str = callback.data.split(":")[-1]
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    new_center_date = current_date + timedelta(days=3)
    is_dev = is_developer(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_main_menu_keyboard(
            is_developer=is_dev, current_center_date=new_center_date
        )
    )


@router.callback_query(F.data.startswith(f"{MENU_PREFIX}scroll_left:"))
async def callback_scroll_left(callback: types.CallbackQuery):
    await callback.answer()
    current_date_str = callback.data.split(":")[-1]
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    new_center_date = current_date - timedelta(days=3)
    is_dev = is_developer(callback.from_user.id)
    await callback.message.edit_reply_markup(
        reply_markup=get_main_menu_keyboard(
            is_developer=is_dev, current_center_date=new_center_date
        )
    )


@router.callback_query(F.data.startswith(CLASS_PREFIX))
async def callback_select_class(callback: types.CallbackQuery):
    await callback.answer()
    if get_user_class(callback.from_user.id):
        await callback.answer(
            "Ваш класс уже установлен. Изменение невозможно.", show_alert=True
        )
        return
    class_num_str = callback.data.split("_")[-1]
    class_num = int(class_num_str)
    await callback.message.edit_text(
        f"Вы выбрали **{class_num}** класс. Теперь выберите букву:",
        reply_markup=get_letter_keyboard(class_num, CLASS_CONFIG),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith(LETTER_PREFIX))
async def callback_select_letter(callback: types.CallbackQuery):
    if get_user_class(callback.from_user.id):
        await callback.answer("Класс уже установлен!", show_alert=True)
        return
    _, _, class_num_str, class_letter = callback.data.split("_")
    class_num = int(class_num_str)
    set_user_class(callback.from_user.id, class_num, class_letter, callback.from_user.username)
    final_class = f"{class_num}{class_letter}"
    await callback.message.edit_text(
        f"🎉 Отлично! Ваш класс **{final_class}** успешно сохранен. "
        "Теперь выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data.startswith(MENU_PREFIX))
async def callback_main_menu(callback: types.CallbackQuery):
    await callback.answer()
    action = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    if action == "dev":
        if is_developer(user_id=user_id):
            await callback.message.edit_text(
                "💻 **Меню Разработчика**",
                parse_mode="Markdown",
                reply_markup=get_developer_menu_keyboard(),
            )
        else:
            await callback.message.answer(
                "⛔️ **Доступ запрещен.** Это меню только для разработчиков.",
                parse_mode="Markdown",
                show_alert=True,
            )
            is_dev = is_developer(user_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_main_menu_keyboard(is_dev)
            )
        return


@router.callback_query(F.data.startswith(BACK_PREFIX))
async def callback_back_action(callback: types.CallbackQuery):
    await callback.answer()

    action = callback.data.split("_")[-1]  # Получаем "main_menu"
    user_id = callback.from_user.id
    is_dev = is_developer(user_id)
    if action == "main-menu":
        # 1. Удаляем предыдущее сообщение (фото с уроками)
        await callback.message.delete()

        # 2. Отправляем НОВОЕ сообщение с Главным меню
        await callback.message.answer(
            "🏠 Главное меню:", reply_markup=get_main_menu_keyboard(is_dev)
        )
    elif action == "ann-menu": # Новый колбэк для возврата из детального объявления
        ann_keyboard = announcements_menu_kb(ANNOUNCEMENTS_DATA) 
        await callback.message.delete()
        await callback.message.answer(
            "📢 **Меню объявлений**\n\nАктуальные новости и обновления:", 
            reply_markup=ann_keyboard, 
            parse_mode="Markdown"
        )
    else:
        await callback.answer("Действие не распознано.")



