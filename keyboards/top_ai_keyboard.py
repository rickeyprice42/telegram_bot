from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_top_ai_categories_keyboard(categories):
    keyboard = []

    for category_key, title in categories:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=title,
                    callback_data=f"top_ai_{category_key}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_top_ai_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к категориям",
                    callback_data="top_ai_back",
                )
            ]
        ]
    )


def get_top_ai_result_keyboard(tools):
    keyboard = []
    medals = ["🥇", "🥈", "🥉"]

    for i, tool in enumerate(tools[:3]):
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

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад к категориям",
                callback_data="top_ai_back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
