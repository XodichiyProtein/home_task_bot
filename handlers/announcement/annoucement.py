from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from states import AnnouncementStates
from config import ANNOUNCEMENTS_DATA, NEXT_ANNOUNCEMENT_ID, ANNOUNCEMENTS_FILE, ANN_PREFIX
from keyboards import announcements_menu_kb, announcement_detail_kb, get_main_menu_keyboard
from db.database import is_developer

import os
import json


router = Router()

# 1 Работа с базой данных связаной с объявлениями
def load_announcements():
    """Загружает объявления из локального JSON-файла."""
    global ANNOUNCEMENTS_DATA, NEXT_ANNOUNCEMENT_ID
    if os.path.exists(ANNOUNCEMENTS_FILE):
        try:
            with open(ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ANNOUNCEMENTS_DATA = data.get('announcements', [])
                # Устанавливаем NEXT_ANNOUNCEMENT_ID
                if ANNOUNCEMENTS_DATA:
                    max_id = max(ann['id'] for ann in ANNOUNCEMENTS_DATA)
                    NEXT_ANNOUNCEMENT_ID = max_id + 1
                else:
                    NEXT_ANNOUNCEMENT_ID = 1
        except (json.JSONDecodeError, FileNotFoundError):
            ANNOUNCEMENTS_DATA = []
            NEXT_ANNOUNCEMENT_ID = 1
    else:
        ANNOUNCEMENTS_DATA = []
        NEXT_ANNOUNCEMENT_ID = 1

def save_announcements():
    """Сохраняет объявления в локальный JSON-файл."""
    data = {'announcements': ANNOUNCEMENTS_DATA}
    with open(ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_next_announcement_id() -> int:
    """Получает следующий ID для нового объявления (имитация DB)."""
    global NEXT_ANNOUNCEMENT_ID
    current_id = NEXT_ANNOUNCEMENT_ID
    NEXT_ANNOUNCEMENT_ID += 1
    return current_id



# 2. Обработка всех колбэков, связанных с объявлениями (view, delete, create_start, ViewMenu)
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
        elif announcement['file_type'] == 'video':
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
    F.photo | F.document | F.video | F.text | F.caption 
)
async def process_announcement_content(message: types.Message, state: FSMContext):
    """Обрабатывает сообщение от разработчика, содержащее файл и/или текст."""
    user_data = await state.get_data()
    announcement_id = user_data.get('announcement_id')
    title = user_data.get('title', f"Объявление #{announcement_id}")
    
    
    text = message.caption or message.text
    file_id = None
    file_type = None

    # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ТИПА ФАЙЛА ---
    if message.photo:
        # фото
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        # Видео
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
        'title': title,
        'text': text if text else "Объявление без текста.",
        'file_id': file_id,
        'file_type': file_type,
    })

    save_announcements()
    await state.clear()
    is_dev = is_developer(message.from_user.id)

    await message.answer(
        f"✅ **Объявление #{announcement_id} успешно создано!**", 
        reply_markup=get_main_menu_keyboard(is_dev), 
        parse_mode="Markdown"
    )
async def start_create_announcement(call: types.CallbackQuery, state: FSMContext):
    """Начинает процесс создания объявления, устанавливая FSM-состояние."""
    
    new_ann_id = get_next_announcement_id()
    await state.set_state(AnnouncementStates.waiting_for_announcement_title) 
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
        is_dev = is_developer(user_id)
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

