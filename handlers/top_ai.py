from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.database import get_categories, get_top_tools_by_category
from keyboards.top_ai_keyboard import get_top_ai_back_keyboard, get_top_ai_categories_keyboard

router = Router()


@router.callback_query((F.data.startswith("top_ai_")) & (F.data != "top_ai_back"))
async def show_top_ai(callback: CallbackQuery):
    category_key = callback.data.replace("top_ai_", "", 1)
    tools = get_top_tools_by_category(category_key)

    if not tools:
        await callback.message.answer("В этой категории пока нет данных.")
        await callback.answer()
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 Лучшие AI\n\n"

    for i, tool in enumerate(tools):
        name = tool["name"]
        favorites = tool["favorites_count"]
        rating = tool["external_rating"]

        text += (
            f"{medals[i]} {name}\n"
            f"⭐ Рейтинг: {rating}\n"
            f"❤️ В избранном: {favorites}\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_top_ai_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "top_ai_back")
async def top_ai_back(callback: CallbackQuery):
    categories = get_categories()
    await callback.message.edit_text(
        "🔥 Лучшие AI\n\nВыберите категорию:",
        reply_markup=get_top_ai_categories_keyboard(categories),
    )
    await callback.answer()
