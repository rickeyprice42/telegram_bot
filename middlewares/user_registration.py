from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from database.models import add_user


class UserRegistrationMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event,
        data: Dict[str, Any]
    ):

        if event.from_user:

            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name

            add_user(user_id, username, first_name)

        return await handler(event, data)