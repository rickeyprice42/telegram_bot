from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile

from database.database import get_categories, get_top_tools_by_category
from keyboards.top_ai_keyboard import get_top_ai_categories_keyboard, get_top_ai_result_keyboard
from utils.image_generator import generate_top_image

router = Router()


@router.callback_query((F.data.startswith("top_ai_")) & (F.data != "top_ai_back"))
async def show_top_ai(callback: CallbackQuery):
    await callback.answer("Генерирую карточку...")

    category_key = callback.data.replace("top_ai_", "", 1)
    tools = get_top_tools_by_category(category_key)

    if not tools:
        await callback.message.answer("В этой категории пока нет данных.")
        return

    categories = {item["category_key"]: item["title"] for item in get_categories()}
    category_title = categories.get(category_key, category_key)
    tools_data = [dict(tool) for tool in tools]

    image_path = await generate_top_image(
        category_name=category_title,
        top3=tools_data,
        output_path=Path("generated") / f"top_{category_key}_{callback.from_user.id}.png",
    )

    await callback.message.answer_photo(
        photo=FSInputFile(image_path),
        caption=f"Топ-3 AI в категории: {category_title}",
        reply_markup=get_top_ai_result_keyboard(tools_data),
    )
    await callback.message.delete()


@router.callback_query(F.data == "top_ai_back")
async def top_ai_back(callback: CallbackQuery):
    await callback.answer()

    categories = get_categories()
    await callback.message.delete()
    await callback.message.answer(
        "🔥 Лучшие AI\n\nВыберите категорию:",
        reply_markup=get_top_ai_categories_keyboard(categories),
    )
