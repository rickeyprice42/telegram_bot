from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_tool_keyboard(
    link: str,
    tool_id: str,
    in_favorites: bool = False,
    category_key: str | None = None,
    page_index: int | None = None,
    total_pages: int | None = None,
) -> InlineKeyboardMarkup:
    second_button = (
        InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=f"rem_{tool_id}")
        if in_favorites
        else InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav_{tool_id}")
    )

    keyboard = [
        [InlineKeyboardButton(text="🔗 Открыть сайт", url=link)],
        [second_button],
    ]

    if category_key is not None and page_index is not None and total_pages is not None:
        prev_index = (page_index - 1) % total_pages
        next_index = (page_index + 1) % total_pages
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"pg:{category_key}:{prev_index}",
                ),
                InlineKeyboardButton(
                    text=f"{page_index + 1}/{total_pages}",
                    callback_data="pg:noop",
                ),
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"pg:{category_key}:{next_index}",
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ К категориям", callback_data="cat_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
