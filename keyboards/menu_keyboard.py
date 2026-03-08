from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS


def get_main_menu(user_id: int):

    keyboard = [
        [KeyboardButton(text="📊 Профиль")],
        [
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="ℹ️ Помощь")
        ]
    ]

    # если пользователь админ — добавляем кнопку админ-панели
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )