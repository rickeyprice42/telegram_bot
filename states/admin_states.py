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


class CategoryAdminState(StatesGroup):
    waiting_for_category_key = State()
    waiting_for_category_title = State()
    waiting_for_new_category_title = State()
