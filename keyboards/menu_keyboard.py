from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_IDS


def get_main_menu(user_id: int):

    keyboard = [
        [KeyboardButton(text="🤖 Подобрать нейросеть")],
        [
            KeyboardButton(text="📚 Каталог нейросетей"),
            KeyboardButton(text="🔥 Лучшие AI")
         ],
        [
            KeyboardButton(text="📊 Профиль"),
            KeyboardButton(text="💎 AI PRO")
            ]
    ]

    # если пользователь админ — добавляем кнопку админ-панели
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )