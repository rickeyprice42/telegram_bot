from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_tool_keyboard(
    link: str,
    tool_id: str,
    in_favorites: bool = False,
    category_key: str | None = None,
    page_index: int | None = None,
    total_pages: int | None = None,
    pager_prefix: str = "pg",
) -> InlineKeyboardMarkup:
    if in_favorites and page_index is not None and pager_prefix == "fp":
        remove_callback = f"remf:{tool_id}:{page_index}"
    else:
        remove_callback = f"rem:{tool_id}"

    second_button = (
        InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=remove_callback)
        if in_favorites
        else InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav:{tool_id}")
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
                    callback_data=f"{pager_prefix}:{category_key}:{prev_index}",
                ),
                InlineKeyboardButton(
                    text=f"{page_index + 1}/{total_pages}",
                    callback_data=f"{pager_prefix}:noop",
                ),
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"{pager_prefix}:{category_key}:{next_index}",
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ К категориям", callback_data="cat_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
