from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.models import add_favorite, get_user_favorites, is_favorite, remove_favorite
from keyboards.catalog_keyboard import get_catalog_keyboard
from keyboards.tool_card_keyboard import get_tool_keyboard
from states.catalog_states import CatalogStates
from utils.ai_catalog import get_categories, load_catalog

router = Router()

FAVORITES_KEY = "__favorites__"


def get_category_tools(category_key: str) -> list[dict]:
    categories = get_categories()
    category = categories.get(category_key)
    if not category:
        return []
    return category.get("tools", [])


def get_favorite_tools(user_id: int) -> list[dict]:
    favorite_ids = get_user_favorites(user_id)
    if not favorite_ids:
        return []

    catalog = load_catalog()
    tools_by_id = {}
    for category in catalog["categories"].values():
        for tool in category.get("tools", []):
            tools_by_id[tool["id"]] = tool

    return [tools_by_id[tool_id] for tool_id in favorite_ids if tool_id in tools_by_id]


def get_tool_by_id(tool_id: str) -> dict | None:
    catalog = load_catalog()
    for category in catalog["categories"].values():
        for tool in category.get("tools", []):
            if tool["id"] == tool_id:
                return tool
    return None


def get_pagination_context(message: Message) -> tuple[str | None, int | None, int | None, str]:
    reply_markup = message.reply_markup
    if not reply_markup:
        return None, None, None, "pg"

    for row in reply_markup.inline_keyboard:
        if len(row) != 3:
            continue

        left_button, center_button, right_button = row
        left_data = left_button.callback_data or ""
        center_data = center_button.callback_data or ""
        right_data = right_button.callback_data or ""

        if not center_data.endswith(":noop"):
            continue
        if ":" not in left_data or ":" not in right_data:
            continue

        pager_prefix, category_key, _ = left_data.split(":", 2)
        if not right_data.startswith(f"{pager_prefix}:{category_key}:"):
            continue

        page_text = center_button.text or ""
        if "/" not in page_text:
            continue

        current_page_raw, total_pages_raw = page_text.split("/", 1)
        try:
            page_index = int(current_page_raw) - 1
            total_pages = int(total_pages_raw)
        except ValueError:
            continue

        return category_key, page_index, total_pages, pager_prefix

    return None, None, None, "pg"


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
    pager_prefix: str = "pg",
):
    caption = f"🤖 <b>{tool['name']}</b>\n\n{tool['description']}"
    reply_markup = get_tool_keyboard(
        tool["link"],
        tool["id"],
        in_favorites=in_favorites,
        category_key=category_key,
        page_index=page_index,
        total_pages=total_pages,
        pager_prefix=pager_prefix,
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


async def refresh_tool_keyboard(callback: CallbackQuery, tool_id: str, in_favorites: bool):
    tool = get_tool_by_id(tool_id)
    if not tool:
        return

    category_key, page_index, total_pages, pager_prefix = get_pagination_context(callback.message)
    reply_markup = get_tool_keyboard(
        tool["link"],
        tool_id,
        in_favorites=in_favorites,
        category_key=category_key,
        page_index=page_index,
        total_pages=total_pages,
        pager_prefix=pager_prefix,
    )
    await callback.message.edit_reply_markup(reply_markup=reply_markup)


async def send_category_page(message: Message, user_id: int, category_key: str, index: int):
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
        pager_prefix="pg",
    )


async def send_favorites_page(message: Message, user_id: int, index: int):
    tools = get_favorite_tools(user_id)
    if not tools:
        await message.answer("У вас пока нет избранных инструментов ⭐")
        return

    safe_index = index % len(tools)
    await send_tool_card(
        message=message,
        user_id=user_id,
        tool=tools[safe_index],
        in_favorites=True,
        category_key=FAVORITES_KEY,
        page_index=safe_index,
        total_pages=len(tools),
        pager_prefix="fp",
    )


@router.message(F.text == "📚 Каталог нейросетей")
async def open_catalog(message: Message, state: FSMContext):
    await send_catalog_menu(message, state)


@router.callback_query(F.data == "cat_menu")
async def catalog_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "cat_favorites")
async def show_favorites_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CatalogStates.category_view)
    await send_favorites_page(callback.message, callback.from_user.id, 0)
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


@router.callback_query(F.data.startswith("fp:"))
async def paginate_favorites(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    if data == "fp:noop":
        await callback.answer()
        return

    _, section_key, page_raw = data.split(":", 2)
    if section_key != FAVORITES_KEY:
        await callback.answer("Ошибка навигации", show_alert=True)
        return

    try:
        page_index = int(page_raw)
    except ValueError:
        await callback.answer("Ошибка навигации", show_alert=True)
        return

    await state.set_state(CatalogStates.category_view)
    await callback.message.delete()
    await send_favorites_page(callback.message, callback.from_user.id, page_index)
    await callback.answer()


@router.callback_query(F.data.startswith("fav:"))
async def add_to_favorites(callback: CallbackQuery):
    tool_id = callback.data.replace("fav:", "", 1)
    user_id = callback.from_user.id

    if is_favorite(user_id, tool_id):
        await callback.answer("Уже в избранном ⭐")
        return

    add_favorite(user_id, tool_id)
    await refresh_tool_keyboard(callback, tool_id, in_favorites=True)
    await callback.answer("Добавлено в избранное ⭐")


@router.callback_query(F.data.startswith("remf:"))
async def remove_from_favorites_paged(callback: CallbackQuery):
    _, tool_id, page_raw = callback.data.split(":", 2)
    user_id = callback.from_user.id

    try:
        page_index = int(page_raw)
    except ValueError:
        await callback.answer("Ошибка удаления", show_alert=True)
        return

    if not remove_favorite(user_id, tool_id):
        await callback.answer("Этого инструмента нет в избранном")
        return

    await callback.message.delete()

    remaining_tools = get_favorite_tools(user_id)
    if not remaining_tools:
        await callback.message.answer("У вас пока нет избранных инструментов ⭐")
        await callback.answer("Удалено из избранного")
        return

    next_index = min(page_index, len(remaining_tools) - 1)
    await send_favorites_page(callback.message, user_id, next_index)
    await callback.answer("Удалено из избранного")


@router.callback_query(F.data.startswith("rem:"))
async def remove_from_favorites(callback: CallbackQuery):
    tool_id = callback.data.replace("rem:", "", 1)
    user_id = callback.from_user.id

    if not remove_favorite(user_id, tool_id):
        await callback.answer("Этого инструмента нет в избранном")
        return

    await refresh_tool_keyboard(callback, tool_id, in_favorites=False)
    await callback.answer("Удалено из избранного")
