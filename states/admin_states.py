from aiogram.fsm.state import State, StatesGroup


class AddTool(StatesGroup):
    name = State()
    description = State()
    link = State()
    category = State()
    image = State()
    use_cases = State()


class RatingState(StatesGroup):
    waiting_for_rating = State()


class UserModerationState(StatesGroup):
    waiting_for_user_id = State()
