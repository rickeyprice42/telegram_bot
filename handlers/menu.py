from aiogram import F, Router
from aiogram.types import Message

from database.database import get_categories as get_top_ai_categories
from database.models import get_user, get_users_count
from keyboards.top_ai_keyboard import get_top_ai_categories_keyboard

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


@router.message(F.text == "🔥 Лучшие AI")
async def show_top_ai_categories(message: Message):
    categories = get_top_ai_categories()

    await message.answer(
        "🔥 Лучшие AI\n\nВыберите категорию:",
        reply_markup=get_top_ai_categories_keyboard(categories),
    )


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    await message.answer("Здесь будут настройки.")


@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Это тестовый бот.\n\n"
        "Функции будут добавляться постепенно."
    )
