from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.ai_picker import get_use_cases


def picker_menu():
    cases = get_use_cases()
    keyboard = []

    for case_key, title, emoji in cases:
        prefix = f"{emoji} " if emoji else ""
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{title}",
                    callback_data=f"pick_case:{case_key}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_picker_level_keyboard(case_key: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Легкая", callback_data=f"pick_level:{case_key}:easy")],
            [InlineKeyboardButton(text="Средняя", callback_data=f"pick_level:{case_key}:medium")],
            [InlineKeyboardButton(text="Сложная", callback_data=f"pick_level:{case_key}:hard")],
            [InlineKeyboardButton(text="⬅️ Назад к задачам", callback_data="picker_back")],
        ]
    )


def get_picker_preference_keyboard(case_key: str, level_tag: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Бесплатная", callback_data=f"pick_pref:{case_key}:{level_tag}:free")],
            [InlineKeyboardButton(text="Быстрая", callback_data=f"pick_pref:{case_key}:{level_tag}:fast")],
            [InlineKeyboardButton(text="Максимальное качество", callback_data=f"pick_pref:{case_key}:{level_tag}:quality")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pick_case:{case_key}")],
        ]
    )


def get_picker_result_keyboard(case_key: str, tools=None):
    keyboard = []
    medals = ["🥇", "🥈", "🥉"]

    for i, tool in enumerate((tools or [])[:3]):
        link = tool.get("link")
        if not link:
            continue

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{medals[i]} {tool['name']}",
                    url=link,
                )
            ]
        )

    keyboard.extend(
        [
            [InlineKeyboardButton(text="🔄 Пройти тест заново", callback_data=f"pick_case:{case_key}")],
            [InlineKeyboardButton(text="⬅️ Назад к задачам", callback_data="picker_back")],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
