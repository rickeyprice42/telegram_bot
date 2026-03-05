from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards.menu_keyboard import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в бота 🚀",
        reply_markup=main_menu
    )