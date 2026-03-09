from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models import add_favorite, get_user_favorites, is_favorite, remove_favorite
from keyboards.catalog_keyboard import get_catalog_keyboard
from keyboards.menu_keyboard import get_main_menu
from keyboards.tool_card_keyboard import get_tool_keyboard
from states.catalog_states import CatalogStates
from utils.ai_catalog import get_categories, load_catalog

router = Router()


def get_category_tools(category_key: str) -> list[dict]:
    categories = get_categories()
    category = categories.get(category_key)
    if not category:
        return []
    return category.get("tools", [])


async def send_catalog_menu(message: Message, state: FSMContext):
    await state.set_state(CatalogStates.catalog_menu)
    await message.answer("Выберите категорию:", reply_markup=get_catalog_keyboard())


async def send_tool_card(
    message: Message,
    user_id: int,
    tool: dict,
    in_favorites: bool = False,
    category_key: str | None = None,
    page_index: int | None = None,
    total_pages: int | None = None,
):
    caption = f"🤖 <b>{tool['name']}</b>\n\n{tool['description']}"
    reply_markup = get_tool_keyboard(
        tool["link"],
        tool["id"],
        in_favorites=in_favorites,
        category_key=category_key,
        page_index=page_index,
        total_pages=total_pages,
    )
    image = tool.get("image")

    if image:
        try:
            await message.answer_photo(
                photo=image,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            return
        except TelegramBadRequest:
            pass

    await message.answer(
        caption,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def send_category_page(
    message: Message,
    user_id: int,
    category_key: str,
    index: int,
):
    tools = get_category_tools(category_key)
    if not tools:
        await message.answer("Категория не найдена", reply_markup=get_catalog_keyboard())
        return

    safe_index = index % len(tools)
    tool = tools[safe_index]
    await send_tool_card(
        message=message,
        user_id=user_id,
        tool=tool,
        in_favorites=is_favorite(user_id, tool["id"]),
        category_key=category_key,
        page_index=safe_index,
        total_pages=len(tools),
    )


async def send_favorites(message: Message, user_id: int):
    favorites = get_user_favorites(user_id)
    if not favorites:
        await message.answer("У вас пока нет избранных инструментов ⭐")
        return

    catalog = load_catalog()
    for category in catalog["categories"].values():
        for tool in category["tools"]:
            if tool["id"] in favorites:
                await send_tool_card(message, user_id, tool, in_favorites=True)


@router.message(F.text == "📚 Каталог нейросетей")
async def open_catalog(message: Message, state: FSMContext):
    await send_catalog_menu(message, state)


@router.callback_query(F.data == "cat_menu")
async def catalog_menu_callback(callback: CallbackQuery, state: FSMContext):
    await send_catalog_menu(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "cat_back")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "cat_favorites")
async def show_favorites_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CatalogStates.catalog_menu)
    await send_favorites(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def show_category_callback(callback: CallbackQuery, state: FSMContext):
    category_key = callback.data.replace("cat_", "", 1)
    tools = get_category_tools(category_key)

    if not tools:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    await state.set_state(CatalogStates.category_view)
    await send_category_page(callback.message, callback.from_user.id, category_key, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("pg:"))
async def paginate_category(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data == "pg:noop":
        await callback.answer()
        return

    _, category_key, page_raw = data.split(":", 2)

    try:
        page_index = int(page_raw)
    except ValueError:
        await callback.answer("Ошибка навигации", show_alert=True)
        return

    await state.set_state(CatalogStates.category_view)
    await callback.message.delete()
    await send_category_page(callback.message, callback.from_user.id, category_key, page_index)
    await callback.answer()


@router.callback_query(F.data.startswith("fav_"))
async def add_to_favorites(callback: CallbackQuery):
    tool_id = callback.data.replace("fav_", "", 1)
    user_id = callback.from_user.id

    if is_favorite(user_id, tool_id):
        await callback.answer("Уже в избранном ⭐")
        return

    add_favorite(user_id, tool_id)
    await callback.answer("Добавлено в избранное ⭐")


@router.callback_query(F.data.startswith("rem_"))
async def remove_from_favorites(callback: CallbackQuery):
    tool_id = callback.data.replace("rem_", "", 1)
    user_id = callback.from_user.id

    if not remove_favorite(user_id, tool_id):
        await callback.answer("Этого инструмента нет в избранном")
        return

    await callback.answer("Удалено из избранного")
    await callback.message.delete()
