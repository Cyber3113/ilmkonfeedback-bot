"""FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    phone = State()
    role = State()


class FeedbackForm(StatesGroup):
    waiting_text = State()
    confirm = State()


class AnswerForm(StatesGroup):
    waiting_answer = State()


class BroadcastForm(StatesGroup):
    waiting_message = State()
    confirm = State()
