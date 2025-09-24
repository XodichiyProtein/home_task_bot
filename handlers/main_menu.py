from states.dev_states import EditHomeworkStates

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from config import (
    CLASS_CONFIG,
    DEVELOPER_IDS,
    CLASS_PREFIX,
    LETTER_PREFIX,
    MENU_PREFIX,
    EDIT_HOMEWORK_PREFIX,
)
from db.database import get_user_class, set_user_class
from keyboards.keyboards import (
    get_class_keyboard,
    get_letter_keyboard,
    get_main_menu_keyboard,
    get_developer_menu_keyboard,
)

from utils.parser import create_schedule_image, get_lesson_numbers, edit_homework
from keyboards.keyboards import get_edit_homework_keyboard

from datetime import datetime, timedelta

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_class = get_user_class(user_id)
    is_dev = user_id in DEVELOPER_IDS

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
    is_dev = callback.from_user.id in DEVELOPER_IDS
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
    is_dev = callback.from_user.id in DEVELOPER_IDS
    await callback.message.edit_reply_markup(
        reply_markup=get_main_menu_keyboard(
            is_developer=is_dev, current_center_date=new_center_date
        )
    )


@router.callback_query(F.data.startswith(CLASS_PREFIX))
async def callback_select_class(callback: types.CallbackQuery):
    await callback.answer()
    if get_user_class(callback.from_user.id):
        await callback.message.edit_text(
            "Ваш класс уже установлен. Изменение невозможно.", reply_markup=None
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
        await callback.answer("Класс уже установлен!")
        await callback.message.edit_text(
            "Ваш класс уже установлен. Изменение невозможно.", reply_markup=None
        )
        return
    _, _, class_num_str, class_letter = callback.data.split("_")
    class_num = int(class_num_str)
    set_user_class(callback.from_user.id, class_num, class_letter)
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
    if action == "dev_access":
        if user_id in DEVELOPER_IDS:
            await callback.message.edit_text(
                "💻 **Меню Разработчика**",
                parse_mode="Markdown",
                reply_markup=get_developer_menu_keyboard(),
            )
        else:
            await callback.message.answer(
                "⛔️ **Доступ запрещен.** Это меню только для разработчиков.",
                parse_mode="Markdown",
            )
            is_dev = user_id in DEVELOPER_IDS
            await callback.message.edit_reply_markup(
                reply_markup=get_main_menu_keyboard(is_dev)
            )
        return


# Обработчик для редактирования ДЗ
@router.callback_query(F.data.startswith(EDIT_HOMEWORK_PREFIX))
async def callback_edit_homework(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    date_str, lesson_number_str = callback.data.split(EDIT_HOMEWORK_PREFIX)[-1].split(
        ":"
    )
    lesson_number = int(lesson_number_str)

    user_id = callback.from_user.id
    user_class = get_user_class(user_id)
    if not user_class:
        return

    class_num, class_letter = user_class

    await state.set_state(EditHomeworkStates.waiting_for_new_homework)
    await state.update_data(
        class_num=class_num,
        class_letter=class_letter,
        date=date_str,
        lesson_number=lesson_number,
    )
    await callback.message.answer(
        f"Введите новое домашнее задание для урока {lesson_number}."
    )


@router.message(EditHomeworkStates.waiting_for_new_homework, F.text)
async def process_new_homework_input(message: types.Message, state: FSMContext):
    user_input = message.text.strip()

    # Check if the user wants to cancel
    if user_input.lower() == "/cancel":
        await state.clear()
        is_dev = message.from_user.id in DEVELOPER_IDS
        await message.answer(
            "Редактирование домашнего задания отменено.",
            reply_markup=get_main_menu_keyboard(is_dev),
        )
        return

    # Retrieve stored data from the FSM context
    data = await state.get_data()
    class_num = data.get("class_num")
    class_letter = data.get("class_letter")
    date_str = data.get("date")
    lesson_number = data.get("lesson_number")

    # Call the function to edit the homework
    success = edit_homework(
        class_num, class_letter, date_str, lesson_number, user_input
    )

    if success:
        await message.answer(
            f"✅ Домашнее задание для урока {lesson_number} успешно обновлено."
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при обновлении домашнего задания. Попробуйте еще раз."
        )

    # Clear the state and return to the main menu
    await state.clear()
    is_dev = message.from_user.id in DEVELOPER_IDS
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_main_menu_keyboard(is_dev)
    )
