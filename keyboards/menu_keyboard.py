from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Профиль"),
            KeyboardButton(text="⚙️ Настройки")
        ],
        [
            KeyboardButton(text="ℹ️ Помощь")
        ]
    ],
    resize_keyboard=True
)