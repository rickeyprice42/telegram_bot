import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.menu import router as menu_router

from database.database import init_db
from middlewares.user_registration import UserRegistrationMiddleware
from handlers.admin import router as admin_router
from middlewares.subscription import SubscriptionMiddleware
from middlewares.antiflood import AntiFloodMiddleware
from utils.logger import LoggingMiddleware, setup_logger

async def main():
    setup_logger()

    # Инициализация базы данных
    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.message.middleware(UserRegistrationMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.message.middleware(AntiFloodMiddleware())
    dp.callback_query.middleware(AntiFloodMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
