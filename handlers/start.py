import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.models import add_user
from keyboards.menu_keyboard import main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Добавляем пользователя в базу
    is_new_user = add_user(user_id, username, first_name)
    logger.info(
        "User saved to DB: user_id=%s username=%s first_name=%s new_user=%s",
        user_id,
        username,
        first_name,
        is_new_user,
    )

    text = (
        f"Привет, {first_name}!\n\n"
        "Добро пожаловать в бота🚀"
    )

    await message.answer(
        text,
        reply_markup=main_menu
    )
