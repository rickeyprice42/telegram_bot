from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from config import CHANNEL_ID
from keyboards.subscription_keyboard import subscribe_keyboard


class SubscriptionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event,
        data: Dict[str, Any]
    ):

        bot = data["bot"]


        if event.text == "/start":
            return await handler(event, data)
        user_id = event.from_user.id

        member = await bot.get_chat_member(CHANNEL_ID, user_id)

        if member.status not in ["member", "administrator", "creator"]:

            await event.answer(
                "📢 Для использования бота подпишитесь на канал.",
                reply_markup=subscribe_keyboard
            )

            return

        return await handler(event, data)