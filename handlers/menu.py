from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "📊 Профиль")
async def profile_handler(message: Message):
    await message.answer("Ваш профиль пока пуст.")


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    await message.answer("Здесь будут настройки.")


@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Это тестовый бот.\n\n"
        "Функции будут добавляться постепенно."
    )