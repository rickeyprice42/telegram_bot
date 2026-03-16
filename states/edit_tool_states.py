from aiogram.fsm.state import State, StatesGroup

class EditTool(StatesGroup):

    choose_tool = State()
    choose_field = State()
    new_value = State()