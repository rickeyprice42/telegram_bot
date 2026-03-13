from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.ai_picker import get_use_cases


def picker_menu():

    cases = get_use_cases()

    keyboard = []

    for case_key, title, emoji in cases:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {title}",
                callback_data=f"pick_{case_key}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)