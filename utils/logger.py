import logging
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from logging.handlers import RotatingFileHandler
import os

logger = logging.getLogger("bot")

def setup_logger():

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # лог в файл
    file_handler = RotatingFileHandler(
        "logs/bot.log",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # лог в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class LoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event,
        data: Dict[str, Any]
    ):

        if hasattr(event, "from_user"):

            user = event.from_user
            user_id = user.id
            username = user.username
            first_name = user.first_name

            action = None

            if hasattr(event, "text"):
                action = event.text

            elif hasattr(event, "data"):
                action = f"callback:{event.data}"

            logger.info(
                "USER_ACTION user_id=%s username=%s name=%s action=%s",
                user_id,
                username,
                first_name,
                action
            )

        return await handler(event, data)