from config import EDIT_HOMEWORK_PREFIX
from keyboards import get_main_menu_keyboard
from states import EditHomeworkStates
from utils.parser import edit_homework
from db.database import get_user_class
from db.database import is_developer

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext


router = Router()

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
async def process_new_homework_input(
    message: types.Message, state: FSMContext, bot: Bot
):
    user_input = message.text.strip()

    try:
        await bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id - 1
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    # Check if the user wants to cancel
    if user_input.lower() == "/cancel":
        await state.clear()
        is_dev = is_developer(message.from_user.id)
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
    is_dev = is_developer(message.from_user.id)
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_main_menu_keyboard(is_dev)
    )
