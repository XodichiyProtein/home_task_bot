from aiogram.fsm.state import State, StatesGroup


class DevStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_admin_id = State()
    waiting_for_confirmation = State()
    waiting_for_admin_id_to_remove = State()


class EditHomeworkStates(StatesGroup):
    waiting_for_new_homework = State()
