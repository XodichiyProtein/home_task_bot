# handlers/dev_menu.py
from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from config import DEVELOPER_IDS, DEV_PREFIX, DOWNLOAD_DIR, MENU_PREFIX
from aiogram.exceptions import TelegramBadRequest 
from states.dev_states import DevStates
from keyboards.keyboards import get_main_menu_keyboard, get_developer_menu_keyboard, get_complaint_keyboard, FB_PREFIX, COMPLAINTS_DATA, save_complaints
from utils.handlers import (
    UPDATE_DEVELOPER_IDS_PERMANENTLY,
    REMOVE_DEVELOPER_ID_PERMANENTLY,
)
from utils.parser import run
import os
import html 

router = Router()


@router.callback_query(F.data.startswith(DEV_PREFIX))
async def callback_developer_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id
        if user_id not in DEVELOPER_IDS:
            await callback.answer(
                "⛔️ Недостаточно прав для этого действия.", show_alert=True
            )
            return
        action = callback.data.split("_")[-1]

        if action == "dev":  # <-- ИСПРАВЛЕНИЕ: ДОБАВЛЕНО ДЕЙСТВИЕ ДЛЯ ОТКРЫТИЯ МЕНЮ
            await callback.message.edit_text(
                "💻 **Меню Разработчика**",
                parse_mode="Markdown",
                reply_markup=get_developer_menu_keyboard(),
            )
            await callback.answer()  # Подтверждаем, что действие выполнено
            return

        elif action == "TableAdd":
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
                "Теперь **введите ID пользователя** у кого надо забрать админ права."
                "\nИли введите `/cancel`, чтобы отменить загрузку.",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif action == "close":
            is_dev = user_id in DEVELOPER_IDS
            await callback.message.edit_text(
                "🏠 Главное меню:", reply_markup=get_main_menu_keyboard(is_dev)
            )
            await callback.answer()
            return

        # Если действие не распознано (не 'dev' и не одно из внутренних действий)
        else:
            await callback.answer("Действие не распознано.")
            return

        await callback.message.edit_text(
            callback.message.text,
            reply_markup=None,
        )
        await callback.answer()

    except Exception as e:
        if "message is not modified" not in str(e):
            print(f"Other error: {e}")
    finally:
        await callback.answer()  # Всплывающее уведомление, если не было другого ответа


@router.message(DevStates.waiting_for_file, F.document)
async def process_file_upload(message: types.Message, state: FSMContext, bot: Bot):
    # 3. Обработчик FSM: Удаляем сообщение пользователя и предыдущий запрос
    try:
        await bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id - 1
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    if message.document.file_size > 20 * 1024 * 1024:
        # 4. Сообщение об ошибке остается сообщением, т.к. это обработчик message
        await message.answer("Файл слишком большой. Отправьте файл меньше 20 МБ.")
        return
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    local_file_name = DOWNLOAD_DIR + file_name
    await bot.download_file(file_path, destination=local_file_name)
    # 3.1 Обработка файла
    run(local_file_name)
    await state.clear()
    is_dev = message.from_user.id in DEVELOPER_IDS

    # 5. Возвращение в Главное меню после обработки
    await message.answer(
        "✅ Файл обработан. Главное меню:",
        reply_markup=get_main_menu_keyboard(is_dev),
    )


@router.message(DevStates.waiting_for_admin_id, F.text)
async def process_admin_id_input(message: types.Message, state: FSMContext, bot: Bot):
    user_input = message.text.strip()
    user_id = message.from_user.id

    # Удаление сообщения-запроса и сообщения-ответа пользователя
    try:
        await bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id - 1
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    if user_input.lower() == "/cancel":
        await state.clear()
        is_dev = user_id in DEVELOPER_IDS
        # 6. Возвращение в Главное меню после отмены
        await message.answer(
            "Добавление администратора отменено. Главное меню:",
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
    is_dev = user_id in DEVELOPER_IDS

    # 7. Возвращение в Главное меню
    await message.answer(
        response_text + "\nВыберите следующее действие:", parse_mode="Markdown"
    )
    await message.answer(
        "🏠 Главное меню:", reply_markup=get_main_menu_keyboard(is_dev)
    )


@router.message(DevStates.waiting_for_file)
async def process_file_upload_invalid(
    message: types.Message, state: FSMContext, bot: Bot
):
    try:
        await bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id - 1
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception:
        pass

    if message.text == "/cancel":
        await state.clear()
        is_dev = message.from_user.id in DEVELOPER_IDS
        # 8. Возвращение в Главное меню после отмены
        await message.answer(
            "Загрузка отменена. Главное меню:",
            reply_markup=get_main_menu_keyboard(is_dev),
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

async def show_next_complaint(callback: types.CallbackQuery, state: FSMContext):
    """Показывает разработчику первую жалобу из очереди COMPLAINTS_DATA."""
    
    await state.clear()
    
    if not COMPLAINTS_DATA:
        # Если жалоб нет, отправляем сообщение об окончании
        try:
            await callback.message.edit_text(
                "🎉 <b>Все жалобы обработаны!</b>",
                reply_markup=get_developer_menu_keyboard(),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            # Игнорируем ошибку, если сообщение уже говорит о том, что все обработано
            if "message is not modified" not in str(e):
                raise e
        return
        
    complaint = COMPLAINTS_DATA[0]
    
    # 1. Экранируем пользовательский текст с помощью стандартного html.escape()
    # Это экранирует <, >, & - единственные символы, ломающие HTML.
    escaped_complaint_text = html.escape(complaint['text'])
    
    # 2. Оборачиваем экранированный текст в тег <code> для отображения "как есть"
    # Тег <code> гарантирует, что \n будут отображены корректно.
    complaint_code_block = f"<code>{escaped_complaint_text}</code>"
    
    # Используем HTML-теги для остальной разметки
    text = (
        f"⚠️ <b>Новая жалоба #{complaint['id']}</b>\n"
        f"👤 ID Пользователя: <code>{complaint['user_id']}</code>\n"
        f"@{complaint.get('username', 'N/A')}\n"
        f"🕒 Дата: {complaint['date']}\n"
        f"---"
        f"\n<b>Содержание:</b>\n{complaint_code_block}" # Вставляем блок кода
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_complaint_keyboard(complaint['id']),
        parse_mode="HTML" # Используем HTML
    )
    
    await state.update_data(current_complaint_id=complaint['id'])
@router.callback_query(F.data == f"{FB_PREFIX}complaints")
async def start_complaint_review(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in DEVELOPER_IDS:
        await callback.answer("⛔️ Недостаточно прав.", show_alert=True)
        return
    
    await callback.answer("Проверка жалоб...")
    await show_next_complaint(callback, state)

@router.callback_query(F.data.startswith(FB_PREFIX))
async def handle_complaint_actions(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    
    user_id = callback.from_user.id
    if user_id not in DEVELOPER_IDS:
        await callback.answer("⛔️ Недостаточно прав.", show_alert=True)
        return

    await callback.answer()
    print(callback.data)
    # Разделяем: fb_skip:<id> -> [fb, skip, <id>]
    action, complaint_id_str = callback.data.split(":")
    action = action.split('_')[-1]
    complaint_id = int(complaint_id_str)
    
    current_state_data = await state.get_data()
    current_complaint_id = current_state_data.get('current_complaint_id')
    
    # Проверка актуальности жалобы
    if current_complaint_id != complaint_id or not COMPLAINTS_DATA or COMPLAINTS_DATA[0]['id'] != complaint_id:
        await callback.answer("⚠️ Эта жалоба устарела или уже обработана. Обновляю.", show_alert=True)
        await show_next_complaint(callback, state)
        return
        
    print(action)
    if action == "back":
        await state.clear()
        await callback.message.edit_text(
            "💻 **Меню Разработчика**",
            parse_mode="Markdown",
            reply_markup=get_developer_menu_keyboard(),
        )
        return
    # --- КОНЕЦ ОБРАБОТЧИКА КНОПКИ НАЗАД ---

    # Для skip, reply, ignore требуется ID
    try:
        complaint_id = int(complaint_id_str)
    except (TypeError, ValueError):
        await callback.answer("❌ Не удалось найти ID жалобы.", show_alert=True)
        return
    if action == "skip":
        # Пропустить: перемещаем текущий элемент в конец списка (имитация очереди)
        skipped_complaint = COMPLAINTS_DATA.pop(0) # Удаляем первый
        COMPLAINTS_DATA.append(skipped_complaint) # Добавляем в конец
        
        await callback.answer("➡️ Жалоба пропущена и перемещена в конец очереди.", show_alert=True)
        save_complaints()
        await show_next_complaint(callback, state)

    elif action == "ignore":
        # Игнорировать: удаляем текущий элемент
        COMPLAINTS_DATA.pop(0)
            
        await callback.answer("🗑️ Жалоба проигнорирована и удалена.", show_alert=True)
        save_complaints()
        await show_next_complaint(callback, state)

    elif action == "reply":
        # Ответить: переходим в FSM-состояние для ввода текста
        await state.update_data(
            target_user_id=COMPLAINTS_DATA[0]['user_id']
        )
        await state.set_state(DevStates.waiting_for_complaint_reply)
        
        await callback.message.edit_text(
            f"💬 **Ответ на жалобу #{complaint_id}:**\n\n"
            f"Введите текст вашего ответа пользователю с ID **{COMPLAINTS_DATA[0]['user_id']}**.\n\n"
            "Для отмены введите `/cancel`."
        )

# --- E. Обработчик получения ответа разработчика ---
@router.message(DevStates.waiting_for_complaint_reply, F.text)
async def process_developer_reply(message: types.Message, state: FSMContext, bot: Bot):
    
    user_data = await state.get_data()
    target_user_id = user_data.get('target_user_id')
    
    is_dev = message.from_user.id in DEVELOPER_IDS

    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Ответ отменен. Жалоба осталась в очереди.",
            reply_markup=get_developer_menu_keyboard()
        )
        return

    # 1. Отправляем ответ пользователю
    reply_text = (
        f"🤖 **Ответ от разработчика**\n\n"
        f"Ваше обращение было рассмотрено. Вот ответ:\n\n"
        f"---"
        f"\n{message.text}"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=reply_text, parse_mode="Markdown")
        
        # 2. Удаляем жалобу из очереди (так как на нее ответили)
        if COMPLAINTS_DATA and COMPLAINTS_DATA[0]['user_id'] == target_user_id:
            COMPLAINTS_DATA.pop(0)
            save_complaints()
            await message.answer("✅ Ответ успешно отправлен, жалоба удалена из очереди.")
        else:
            # Если жалоба была удалена другим разработчиком, просто подтверждаем отправку ответа
            await message.answer("⚠️ Ответ отправлен, но жалоба не найдена в начале очереди.")
            
    except Exception as e:
        await message.answer(f"❌ **Ошибка при отправке ответа пользователю:** {e}")
        # Не удаляем жалобу, если не смогли ответить
        
    await state.clear()
    
    # 3. Возвращаемся в меню разработчика
    await message.answer("Выберите следующее действие:", 
                         reply_markup=get_developer_menu_keyboard())      