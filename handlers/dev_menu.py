# handlers/dev_menu.py
from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from config import DEVELOPER_IDS, DEV_PREFIX, DOWNLOAD_DIR, MENU_PREFIX
from states.dev_states import DevStates
from keyboards.keyboards import get_main_menu_keyboard, get_developer_menu_keyboard
from utils.handlers import (
    UPDATE_DEVELOPER_IDS_PERMANENTLY,
    REMOVE_DEVELOPER_ID_PERMANENTLY,
)
from utils.parser import run
import os

router = Router()


@router.callback_query(F.data.startswith(DEV_PREFIX))
async def callback_developer_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id
        if user_id not in DEVELOPER_IDS:
            await callback.answer("⛔️ Недостаточно прав для этого действия.")
            return
        await callback.answer()
        action = callback.data.split("_")[-1]

        if action == "TableAdd":
            await state.set_state(DevStates.waiting_for_file)
            await callback.message.answer(
                "Теперь **отправьте мне файл**."
                "\nИли введите `/cancel`, чтобы отменить загрузку.",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif action == "AdminAdd":
            await state.set_state(DevStates.waiting_for_admin_id)
            await callback.message.answer(
                "Теперь **введите ID пользователя** кому надо выдать админ права."
                "\nИли введите `/cancel`, чтобы отменить загрузку.",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif action == "AdminRemove":
            await state.set_state(DevStates.waiting_for_admin_id_to_remove)
            await callback.message.answer(
                "Теперь **введите ID пользователя**у кого надо забрать админ права."
                "\nИли введите `/cancel`, чтобы отменить загрузку.",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif action == "close":
            is_dev = user_id in DEVELOPER_IDS
            await callback.message.edit_text(
                "🏠 Главное меню:", reply_markup=get_main_menu_keyboard(is_dev)
            )
            return

        if action not in ["upload_file", "close"]:
            await callback.message.edit_reply_markup(
                reply_markup=get_developer_menu_keyboard()
            )
    except Exception as e:
        if "message is not modified" not in str(e):
            print(f"Other error: {e}")
    finally:
        await callback.answer()


@router.message(DevStates.waiting_for_file, F.document)
async def process_file_upload(message: types.Message, state: FSMContext, bot: Bot):
    if message.document.file_size > 20 * 1024 * 1024:
        await message.answer("Файл слишком большой. Отправьте файл меньше 20 МБ.")
        return
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    local_file_name = DOWNLOAD_DIR + file_name
    await bot.download_file(file_path, destination=local_file_name)
    await message.answer(
        f"✅ Файл **{file_name}** ({file_id}) успешно получен.\n"
        "Запускаю внутреннюю обработку...",
        parse_mode="Markdown",
    )
    # 3.1 Обработка файла
    run(local_file_name)
    await state.clear()
    is_dev = message.from_user.id in DEVELOPER_IDS
    await message.answer(
        "Файл обработан. Выберите следующее действие:",
        reply_markup=get_main_menu_keyboard(is_dev),
    )


@router.message(DevStates.waiting_for_admin_id, F.text)
async def process_admin_id_input(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    if user_input.lower() == "/cancel":
        await state.clear()
        is_dev = message.from_user.id in DEVELOPER_IDS
        await message.answer(
            "Добавление администратора отменено.",
            reply_markup=get_main_menu_keyboard(is_dev),
        )
        return
    try:
        new_admin_id = int(user_input)
    except ValueError:
        await message.answer(
            f"❌ Некорректный ввод. **ID должен быть целым числом**."
            f"\nПожалуйста, введите корректный ID или `/cancel`.",
            parse_mode="Markdown",
        )
        return
    if new_admin_id in DEVELOPER_IDS:
        response_text = (
            f"❗️ Пользователь с ID **{new_admin_id}** уже является администратором."
        )
    else:
        UPDATE_DEVELOPER_IDS_PERMANENTLY(new_admin_id, DEVELOPER_IDS)
        response_text = f"✅ Пользователь с ID **{new_admin_id}** успешно добавлен в список администраторов (временно)."
    await state.clear()
    is_dev = message.from_user.id in DEVELOPER_IDS
    await message.answer(response_text, parse_mode="Markdown")
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_main_menu_keyboard(is_dev)
    )


@router.message(DevStates.waiting_for_file)
async def process_file_upload_invalid(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        is_dev = message.from_user.id in DEVELOPER_IDS
        await message.answer(
            "Загрузка отменена.", reply_markup=get_main_menu_keyboard(is_dev)
        )
        return
    await message.answer("Пожалуйста, отправьте именно **документ** (файл).")


@router.message(DevStates.waiting_for_admin_id_to_remove, F.text)
async def process_admin_id_remove(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    user_id = message.from_user.id
    if user_input.lower() == "/cancel":
        await state.clear()
        is_dev = user_id in DEVELOPER_IDS
        await message.answer(
            "Удаление администратора отменено.",
            reply_markup=get_main_menu_keyboard(is_dev),
        )
        return
    try:
        remove_admin_id = int(user_input)
    except ValueError:
        await message.answer("❌ Некорректный ввод. ID должен быть целым числом.")
        return
    if remove_admin_id == user_id:
        await message.answer(
            "❌ Вы не можете удалить административные права у самого себя!"
        )
        return
    if REMOVE_DEVELOPER_ID_PERMANENTLY(remove_admin_id, DEVELOPER_IDS):
        response_text = f"✅ Пользователь с ID **{remove_admin_id}** успешно удален из администраторов."
    else:
        response_text = f"❗️ Пользователь с ID **{remove_admin_id}** не найден в списке администраторов."
    await state.clear()
    is_dev = user_id in DEVELOPER_IDS
    await message.answer(response_text, parse_mode="Markdown")
    await message.answer(
        "Выберите следующее действие:", reply_markup=get_main_menu_keyboard(is_dev)
    )
