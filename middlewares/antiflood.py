import time
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable


class AntiFloodMiddleware(BaseMiddleware):

    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.users = {}

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event,
        data: Dict[str, Any]
    ):

        if not hasattr(event, "from_user"):
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()

        last_time = self.users.get(user_id, 0)

        if current_time - last_time < self.delay:
            return

        self.users[user_id] = current_time

        return await handler(event, data)