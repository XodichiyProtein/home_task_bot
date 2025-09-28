from aiogram import types, Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import FB_PREFIX, COMPLAINTS_FILE, COMPLAINTS_DATA, NEXT_COMPLAINT_ID
from states import FeedbackStates, DevStates
from keyboards import get_main_menu_keyboard, get_developer_menu_keyboard, get_complaint_keyboard
from db.database import is_developer

import json
import os
import html
from datetime import datetime

router = Router()



def load_complaints():
    """Загружает жалобы из локального JSON-файла."""
    global COMPLAINTS_DATA, NEXT_COMPLAINT_ID
    if os.path.exists(COMPLAINTS_FILE):
        try:
            with open(COMPLAINTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                COMPLAINTS_DATA = data.get('complaints', [])
                if COMPLAINTS_DATA:
                    max_id = max(c['id'] for c in COMPLAINTS_DATA)
                    NEXT_COMPLAINT_ID = max_id + 1
                else:
                    NEXT_COMPLAINT_ID = 1
        except (json.JSONDecodeError, FileNotFoundError):
            COMPLAINTS_DATA = []
            NEXT_COMPLAINT_ID = 1
    else:
        COMPLAINTS_DATA = []
        NEXT_COMPLAINT_ID = 1

def save_complaints():
    """Сохраняет жалобы в локальный JSON-файл."""
    data = {'complaints': COMPLAINTS_DATA}
    with open(COMPLAINTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_complaint_id() -> int:
    """Получает следующий ID для новой жалобы."""
    global NEXT_COMPLAINT_ID
    current_id = NEXT_COMPLAINT_ID
    NEXT_COMPLAINT_ID += 1
    return current_id

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

@router.message(FeedbackStates.waiting_for_feedback, F.text)
async def process_user_feedback(message: types.Message, state: FSMContext):
    
    user_id = message.from_user.id
    is_dev = is_developer(user_id)

    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Отправка обратной связи отменена.", 
            reply_markup=get_main_menu_keyboard(is_dev)
        )
        return

    complaint_id = get_next_complaint_id()
    
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
            if "message is not modified" not in str(e):
                raise e
        return
        
    complaint = COMPLAINTS_DATA[0]
    
    escaped_complaint_text = html.escape(complaint['text'])
    
    complaint_code_block = f"<code>{escaped_complaint_text}</code>"
    
    text = (
        f"⚠️ <b>Новая жалоба #{complaint['id']}</b>\n"
        f"👤 ID Пользователя: <code>{complaint['user_id']}</code>\n"
        f"@{complaint.get('username', 'N/A')}\n"
        f"🕒 Дата: {complaint['date']}\n"
        f"---"
        f"\n<b>Содержание:</b>\n{complaint_code_block}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_complaint_keyboard(complaint['id']),
        parse_mode="HTML"
    )
    
    await state.update_data(current_complaint_id=complaint['id'])
@router.callback_query(F.data == f"{FB_PREFIX}complaints")
async def start_complaint_review(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if is_developer(user_id):
        await callback.answer("⛔️ Недостаточно прав.", show_alert=True)
        return
    
    await callback.answer("Проверка жалоб...")
    await show_next_complaint(callback, state)

@router.callback_query(F.data.startswith(FB_PREFIX))
async def handle_complaint_actions(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    
    user_id = callback.from_user.id
    if is_developer(user_id):
        await callback.answer("⛔️ Недостаточно прав.", show_alert=True)
        return

    await callback.answer()

    action, complaint_id_str = callback.data.split(":")
    action = action.split('_')[-1]
    complaint_id = int(complaint_id_str)
    
    current_state_data = await state.get_data()
    current_complaint_id = current_state_data.get('current_complaint_id')
    
    if current_complaint_id != complaint_id or not COMPLAINTS_DATA or COMPLAINTS_DATA[0]['id'] != complaint_id:
        await callback.answer("⚠️ Эта жалоба устарела или уже обработана. Обновляю.", show_alert=True)
        await show_next_complaint(callback, state)
        return
        
    if action == "back":
        await state.clear()
        await callback.message.edit_text(
            "💻 **Меню Разработчика**",
            parse_mode="Markdown",
            reply_markup=get_developer_menu_keyboard(),
        )
        return

    try:
        complaint_id = int(complaint_id_str)
    except (TypeError, ValueError):
        await callback.answer("❌ Не удалось найти ID жалобы.", show_alert=True)
        return
    if action == "skip":
        skipped_complaint = COMPLAINTS_DATA.pop(0)
        COMPLAINTS_DATA.append(skipped_complaint)
        
        await callback.answer("➡️ Жалоба пропущена и перемещена в конец очереди.", show_alert=True)
        save_complaints()
        await show_next_complaint(callback, state)

    elif action == "ignore":
        COMPLAINTS_DATA.pop(0)
            
        await callback.answer("🗑️ Жалоба проигнорирована и удалена.", show_alert=True)
        save_complaints()
        await show_next_complaint(callback, state)

    elif action == "reply":
        await state.update_data(
            target_user_id=COMPLAINTS_DATA[0]['user_id']
        )
        await state.set_state(DevStates.waiting_for_complaint_reply)
        
        await callback.message.edit_text(
            f"💬 **Ответ на жалобу #{complaint_id}:**\n\n"
            f"Введите текст вашего ответа пользователю с ID **{COMPLAINTS_DATA[0]['user_id']}**.\n\n"
            "Для отмены введите `/cancel`."
        )

@router.message(DevStates.waiting_for_complaint_reply, F.text)
async def process_developer_reply(message: types.Message, state: FSMContext, bot: Bot):
    
    user_data = await state.get_data()
    target_user_id = user_data.get('target_user_id')
    
    is_dev = is_developer(message.from_user.id)

    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Ответ отменен. Жалоба осталась в очереди.",
            reply_markup=get_developer_menu_keyboard()
        )
        return

    reply_text = (
        f"🤖 **Ответ от разработчика**\n\n"
        f"Ваше обращение было рассмотрено. Вот ответ:\n\n"
        f"---"
        f"\n{message.text}"
    )
    
    try:
        await bot.send_message(chat_id=target_user_id, text=reply_text, parse_mode="Markdown")
        
        if COMPLAINTS_DATA and COMPLAINTS_DATA[0]['user_id'] == target_user_id:
            COMPLAINTS_DATA.pop(0)
            save_complaints()
            await message.answer("✅ Ответ успешно отправлен, жалоба удалена из очереди.")
        else:
            await message.answer("⚠️ Ответ отправлен, но жалоба не найдена в начале очереди.")
            
    except Exception as e:
        await message.answer(f"❌ **Ошибка при отправке ответа пользователю:** {e}")
        
    await state.clear()
    
    await message.answer("Выберите следующее действие:", reply_markup=get_developer_menu_keyboard())      
