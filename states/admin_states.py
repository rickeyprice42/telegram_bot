from aiogram.fsm.state import State, StatesGroup


class AddTool(StatesGroup):
    name = State()
    description = State()
    link = State()
    category = State()
    image = State()


class RatingState(StatesGroup):
    waiting_for_rating = State()


class UserModerationState(StatesGroup):
    waiting_for_user_id = State()
