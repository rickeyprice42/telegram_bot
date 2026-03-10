from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.ai_catalog import get_categories


def get_catalog_keyboard() -> InlineKeyboardMarkup:
    categories = get_categories()
    keyboard = []

    for category_key, category in categories.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=category["title"],
                    callback_data=f"cat_{category_key}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⭐ Избранное", callback_data="cat_favorites")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
