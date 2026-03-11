from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_top_ai_categories_keyboard(categories):

    keyboard = []

    for category_key, title in categories:

        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"top_ai_{category_key}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_top_ai_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к категориям",
                    callback_data="top_ai_back"
                )
            ]
        ]
    )
