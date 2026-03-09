from aiogram.fsm.state import StatesGroup, State


class CatalogStates(StatesGroup):
    catalog_menu = State()
    category_view = State()