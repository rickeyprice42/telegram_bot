from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import CHANNEL_ID

channel_username = CHANNEL_ID.replace("@", "")

subscribe_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📣 Подписаться",
                url=f"https://t.me/{channel_username}",
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Проверить подписку",
                callback_data="check_subscription",
            )
        ],
    ]
)
