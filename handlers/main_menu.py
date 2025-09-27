from states.dev_states import EditHomeworkStates, AnnouncementStates, FeedbackStates

from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

import aiogram

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup 
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
    announcements_menu_kb,
    announcement_detail_kb,
    get_next_announcement_id,
    save_announcements,
    get_edit_homework_keyboard,
    get_next_complaint_id,
    save_complaints,
    FB_PREFIX, 
    BACK_PREFIX,
    ANN_PREFIX,
    COMPLAINTS_DATA,
    ANNOUNCEMENTS_DATA,
)

from utils.parser import create_schedule_image, get_lesson_numbers, edit_homework

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
    if action == "dev":
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
                show_alert=True,
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


@router.callback_query(F.data.startswith(BACK_PREFIX))
async def callback_back_action(callback: types.CallbackQuery):
    await callback.answer()

    action = callback.data.split("_")[-1]  # Получаем "main_menu"
    user_id = callback.from_user.id
    is_dev = user_id in DEVELOPER_IDS
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



# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---
def is_developer(user_id: int) -> bool:
    """Проверяет, является ли пользователь разработчиком."""
    # Используем вашу существующую константу
    return user_id in DEVELOPER_IDS 


# 2. Обработка всех колбэков, связанных с объявлениями (view, delete, create_start)
@router.callback_query(F.data.startswith(ANN_PREFIX))
async def handle_announcement_callbacks(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    
    data_suffix = call.data[len(ANN_PREFIX):] 
    
    parts = data_suffix.split(':', 1)
    action = parts[0] # 'view', 'delete', 'create_start', 'no_ann'
    
    await call.answer()
    
    if action == "view":
        if len(parts) == 2:
            announcement_id = int(parts[1])
            await view_announcement_detail(call, announcement_id)
        else:
            await call.answer("❌ Ошибка: Неверный формат объявления (отсутствует ID).", show_alert=True)
    
    if action == 'ViewMenu':
        await call.message.edit_text(
            "📢 **Меню объявлений**\n\nАктуальные новости и обновления:", 
            reply_markup=announcements_menu_kb(ANNOUNCEMENTS_DATA), 
            parse_mode="Markdown"
        )
        return
    
    elif action == "delete":
        if is_developer(user_id):
            if len(parts) == 2:
                announcement_id = int(parts[1])
                await delete_announcement(call, announcement_id)
            else:
                await call.answer("❌ Ошибка: Неверный формат ID для удаления.", show_alert=True)
        else:
            await call.answer("⛔️ Недостаточно прав.", show_alert=True)
            
    elif action == "CreateStart":
        if is_developer(user_id):
            await start_create_announcement(call, state)
        else:
            await call.answer("⛔️ Недостаточно прав.", show_alert=True)
            
    elif action == "no_ann":
        await call.answer("Нет актуальных объявлений.", show_alert=True)
        

# 4. Обработка контента (Файл + Текст)
@router.message(AnnouncementStates.waiting_for_announcement_content, F.text.lower() == "/cancel")
async def cancel_announcement_creation(message: types.Message, state: FSMContext):
    """Отмена создания объявления."""
    await state.clear()
    await message.answer("❌ Создание объявления отменено.")

# 5. Показать детальное объявление (файл + текст)
async def view_announcement_detail(call: types.CallbackQuery, announcement_id: int):
    """Показывает детальное объявление (файл + текст)."""
    announcement = next((a for a in ANNOUNCEMENTS_DATA if a['id'] == announcement_id), None)
    
    if not announcement:
        await call.answer("❌ Объявление не найдено. Обновляю меню.", show_alert=True)
        # Удаляем текущее сообщение
        await call.message.delete() 
        
        # Отправляем новое сообщение с меню объявлений
        await call.bot.send_message(
            chat_id=call.message.chat.id, 
            text="📢 **Меню объявлений**\n\nАктуальные новости и обновления:", 
            reply_markup=announcements_menu_kb(),
            parse_mode="Markdown"
        )
        return

    dev_status = is_developer(call.from_user.id)
    kb = announcement_detail_kb(announcement_id, is_developer=dev_status)
    
    title = announcement.get('title', f"Объявление #{announcement_id}")
    caption = f"📣 **{title}**\n\n{announcement['text']}"
    

    await call.message.delete()
    
    if announcement['file_id']:
        if announcement['file_type'] == 'photo':
            await call.bot.send_photo(
                chat_id=call.message.chat.id, 
                photo=announcement['file_id'], 
                caption=caption, 
                reply_markup=kb, 
                parse_mode="Markdown"
            )
        elif announcement['file_type'] == 'video': # <-- НОВЫЙ ТИП: ВИДЕО
            await call.bot.send_video(
                chat_id=call.message.chat.id, 
                video=announcement['file_id'], 
                caption=caption, 
                reply_markup=kb,
                parse_mode="Markdown"
            )
        elif announcement['file_type'] == 'document':
            await call.bot.send_document(
                chat_id=call.message.chat.id, 
                document=announcement['file_id'], 
                caption=caption, 
                reply_markup=kb, 
                parse_mode="Markdown"
            )
    else:
        # Если нет файла, просто отправляем текст
        await call.message.bot.send_message(
            chat_id=call.message.chat.id, 
            text=caption, 
            reply_markup=kb, 
            parse_mode="Markdown"
        )
async def delete_announcement(call: types.CallbackQuery, announcement_id: int):
    """
    Удаляет объявление. 
    Использует delete + send_message для надежной обработки медиасообщений.
    """
    global ANNOUNCEMENTS_DATA
    
    original_len = len(ANNOUNCEMENTS_DATA)
    
    ANNOUNCEMENTS_DATA = [a for a in ANNOUNCEMENTS_DATA if a['id'] != announcement_id]
    print(len(ANNOUNCEMENTS_DATA))
    # Ответ пользователю
    if len(ANNOUNCEMENTS_DATA) < original_len:
        
        save_announcements()

        new_kb = announcements_menu_kb(ANNOUNCEMENTS_DATA)
        
        await call.message.delete()
        
        final_text = (
            f"🗑️ **Объявление #{announcement_id} успешно удалено!**\n\n"
            "📢 **Меню объявлений**\n\nАктуальные новости и обновления:"
        )
        
        await call.bot.send_message(
            chat_id=call.message.chat.id,
            text=final_text, 
            reply_markup=new_kb, 
            parse_mode="Markdown"
        )
    else:
        await call.answer(f"❌ Объявление #{announcement_id} не найдено для удаления.", show_alert=True)

@router.message(
    AnnouncementStates.waiting_for_announcement_content, 
    F.photo | F.document | F.video | F.text | F.caption # <-- ДОБАВЛЕНО F.video
)
async def process_announcement_content(message: types.Message, state: FSMContext):
    """Обрабатывает сообщение от разработчика, содержащее файл и/или текст."""
    user_data = await state.get_data()
    announcement_id = user_data.get('announcement_id')
    title = user_data.get('title', f"Объявление #{announcement_id}") # <-- ПОЛУЧАЕМ НАЗВАНИЕ
    
    
    text = message.caption or message.text
    file_id = None
    file_type = None

    # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ТИПА ФАЙЛА ---
    if message.photo:
        # Берем фото лучшего качества
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        # Новый тип: Видео
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        # Документ (если это не фото/видео)
        file_id = message.document.file_id
        file_type = 'document'
    # ------------------------------------
    
    if not text and not file_id:
        await message.reply("⚠️ Объявление должно содержать хотя бы текст или файл с подписью. Попробуйте снова или введите `/cancel`.")
        return

    # Сохранение объявления
    ANNOUNCEMENTS_DATA.append({
        'id': announcement_id,
        'title': title, # <-- СОХРАНЯЕМ НАЗВАНИЕ
        'text': text if text else "Объявление без текста.",
        'file_id': file_id,
        'file_type': file_type,
    })

    save_announcements()
    await state.clear()
    
    is_dev = message.from_user.id in DEVELOPER_IDS
    await message.answer(
        f"✅ **Объявление #{announcement_id} успешно создано!**", 
        reply_markup=get_main_menu_keyboard(is_dev), 
        parse_mode="Markdown"
    )
async def start_create_announcement(call: types.CallbackQuery, state: FSMContext):
    """Начинает процесс создания объявления, устанавливая FSM-состояние."""
    
    # Сохраняем ID нового объявления и переходим к ожиданию ЗАГОЛОВКА
    new_ann_id = get_next_announcement_id()
    await state.set_state(AnnouncementStates.waiting_for_announcement_title) # <-- ПЕРЕХОД К ЗАГОЛОВКУ
    await state.update_data(announcement_id=new_ann_id)
    
    await call.message.edit_text(
        f"📝 **Создание объявления #{new_ann_id}**\n\n"
        "**Введите название (заголовок)** объявления. \n\n"
        "Для отмены введите `/cancel`.", 
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(AnnouncementStates.waiting_for_announcement_title, F.text)
async def process_announcement_title(message: types.Message, state: FSMContext):
    """Обрабатывает введенный заголовок и переводит в состояние ожидания контента."""
    user_id = message.from_user.id
    
    if message.text.lower() == "/cancel":
        await state.clear()
        is_dev = user_id in DEVELOPER_IDS
        await message.answer("❌ Создание объявления отменено.", reply_markup=get_main_menu_keyboard(is_dev))
        return

    title = message.text.strip()
    
    await state.update_data(title=title)
    await state.set_state(AnnouncementStates.waiting_for_announcement_content)

    # Просим контент
    await message.answer(
        "📝 **Название сохранено.**\n\n"
        "Теперь отправьте **файл** (фото/видео/документ) и **текст** объявления в одном сообщении. \n"
        "Текст (подпись) станет основным содержанием объявления. \n\n"
        "Для отмены введите `/cancel`.",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == f"{FB_PREFIX}connection")
async def start_feedback_process(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    await state.set_state(FeedbackStates.waiting_for_feedback)
    
    await call.message.edit_text(
        "✍️ **Обратная связь**\n\n"
        "Здесь вы можете написать **жалобу, предложение или идею** для улучшения бота. "
        "Ваше сообщение будет анонимным для других пользователей, но я увижу ваш ID и имя пользователя.\n\n"
        "Введите ваше сообщение или введите `/cancel` для отмены.",
        parse_mode="Markdown"
    )

# --- 2. Обработчик получения текста обратной связи ---
@router.message(FeedbackStates.waiting_for_feedback, F.text)
async def process_user_feedback(message: types.Message, state: FSMContext):
    
    user_id = message.from_user.id
    is_dev = user_id in DEVELOPER_IDS

    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Отправка обратной связи отменена.", 
            reply_markup=get_main_menu_keyboard(is_dev)
        )
        return

    complaint_id = get_next_complaint_id()
    
    # Сохраняем жалобу
    COMPLAINTS_DATA.append({
        'id': complaint_id,
        'user_id': user_id,
        'username': message.from_user.username or 'N/A',
        'text': message.text,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    save_complaints()
    
    await state.clear()
    await message.answer(
        "✅ Ваше сообщение принято и будет рассмотрено разработчиком. Спасибо за вашу помощь!", 
        reply_markup=get_main_menu_keyboard(is_dev)
    )
