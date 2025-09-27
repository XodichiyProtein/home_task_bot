from aiogram.fsm.state import State, StatesGroup


class DevStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_admin_id = State()
    waiting_for_confirmation = State()
    waiting_for_admin_id_to_remove = State()
    waiting_for_complaint_reply = State()


class EditHomeworkStates(StatesGroup):
    waiting_for_new_homework = State()

# --- FSM СОСТОЯНИЯ ДЛЯ ОБЪЯВЛЕНИЙ ---
class AnnouncementStates(StatesGroup):
    """Состояния для процесса создания объявления."""
    waiting_for_announcement_content = State()
    waiting_for_announcement_title = State()

class FeedbackStates(StatesGroup):
    """Состояния для процесса отправки обратной связи."""
    waiting_for_feedback = State()