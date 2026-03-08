from aiogram import Router, F
from aiogram.types import Message
from database.models import get_users_count, get_user

router = Router()


@router.message(F.text == "📊 Профиль")
async def profile_handler(message: Message):

    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.answer("Пользователь не найден.")
        return

    text = (
        "👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: {user['user_id']}\n"
        f"👤 Username: @{user['username']}\n"
        f"📅 Дата регистрации: {user['date_joined']}"
    )

    await message.answer(text)

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    await message.answer("Здесь будут настройки.")


@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Это тестовый бот.\n\n"
        "Функции будут добавляться постепенно."
    )