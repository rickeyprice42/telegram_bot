import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.menu import router as menu_router

from database.database import init_db


async def main():
    logging.basicConfig(level=logging.INFO)

    # Инициализация базы данных
    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(menu_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
