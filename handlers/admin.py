import asyncio
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS
from database.database import (
    add_category,
    add_tool,
    category_exists,
    count_tools_in_category,
    delete_category,
    delete_tool,
    generate_unique_tool_id,
    get_all_tools,
    get_tool_by_id,
    get_tool_category_keys,
    get_tool_use_case_keys,
    get_use_cases,
    save_tool_rating,
    save_tool_categories,
    save_tool_use_cases,
    update_category_title,
    update_tool_field,
)
from database.models import ban_user, get_all_users, get_users_count, unban_user
from keyboards.catalog_keyboard import get_catalog_keyboard
from states.admin_states import AddTool, CategoryAdminState, RatingState, UserModerationState
from states.broadcast_state import BroadcastState
from states.catalog_states import CatalogStates
from utils.ai_catalog import get_categories
from states.edit_tool_states import EditTool

router = Router()


def get_use_cases_prompt() -> str:
    use_cases = get_use_cases()
    lines = [
        "Введите ключи задач через запятую.",
        "Если задачи пока не нужны, отправьте `-`.",
        "",
        "Доступные задачи:",
    ]

    for case_key, title, emoji in use_cases:
        prefix = f"{emoji} " if emoji else ""
        lines.append(f"- {case_key} — {prefix}{title}")

    return "\n".join(lines)


def get_category_keys_prompt() -> str:
    categories = get_categories()
    lines = [
        "Введите ключи категорий через запятую.",
        "",
        "Доступные категории:",
    ]

    for category_key, category in categories.items():
        lines.append(f"- {category_key} — {category['title']}")

    return "\n".join(lines)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="❌ Удалить нейросеть", callback_data="admin_delete_tool"),
            ],
            [
                InlineKeyboardButton(text="➕ Добавить нейросеть", callback_data="admin_add_tool"),
                InlineKeyboardButton(text="✏ Редактировать нейросеть", callback_data="admin_edit_tool")
            ],
            [InlineKeyboardButton(text="🗂 Категории каталога", callback_data="admin_manage_categories")],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="⭐ Обновить рейтинг AI", callback_data="admin_update_rating"),
            ],
            [
                InlineKeyboardButton(text="⛔ Бан", callback_data="admin_ban_user"),
                InlineKeyboardButton(text="✅ Разбан", callback_data="admin_unban_user"),
            ],
        ]
    )


def get_add_tool_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_cancel_add_tool")]
        ]
    )


def get_broadcast_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена рассылки", callback_data="admin_cancel_broadcast")]
        ]
    )


def get_rating_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в админ-панель", callback_data="admin_panel")]
        ]
    )


def get_user_moderation_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в админ-панель", callback_data="admin_panel")]
        ]
    )


def get_category_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_category_add")],
            [InlineKeyboardButton(text="✏ Переименовать категорию", callback_data="admin_category_rename")],
            [InlineKeyboardButton(text="❌ Удалить категорию", callback_data="admin_category_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")],
        ]
    )


def get_category_action_keyboard(callback_prefix: str, back_callback: str = "admin_manage_categories") -> InlineKeyboardMarkup:
    categories = get_categories()
    keyboard = []

    for category_key, category in categories.items():
        tools_count = len(category.get("tools", []))
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{category['title']} ({tools_count})",
                    callback_data=f"{callback_prefix}:{category_key}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_categories_keyboard() -> InlineKeyboardMarkup:
    categories = get_categories()
    keyboard = []

    for category_key, category in categories.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=category["title"],
                    callback_data=f"admin_del_cat:{category_key}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_tools_keyboard(category_key: str) -> InlineKeyboardMarkup:
    categories = get_categories()
    category = categories.get(category_key)
    keyboard = []

    if category:
        for tool in category.get("tools", []):
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=tool["name"],
                        callback_data=f"admin_del_tool:{tool['id']}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton(text="⬅️ К категориям", callback_data="admin_delete_tool")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rating_tools_keyboard() -> InlineKeyboardMarkup:
    tools = get_all_tools()
    keyboard = []

    for tool in tools:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=tool["name"],
                    callback_data=f"rating_tool:{tool['tool_id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_panel_text() -> str:
    return (
        "🔐 <b>Админ-панель</b>\n\n"
        "Доступные команды:\n"
        "📊 /stats — статистика\n"
        "📢 /broadcast — рассылка"
    )


def get_edit_tools_keyboard() -> InlineKeyboardMarkup:
    tools = get_all_tools()
    keyboard = []

    for tool in tools:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=tool["name"],
                    callback_data=f"edit_tool:{tool['tool_id']}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_fields_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Название", callback_data="edit_field:name")],
            [InlineKeyboardButton(text="Описание", callback_data="edit_field:description")],
            [InlineKeyboardButton(text="Ссылка", callback_data="edit_field:link")],
            [InlineKeyboardButton(text="Изображение", callback_data="edit_field:image")],
            [InlineKeyboardButton(text="Категория", callback_data="edit_field:category")],
            [InlineKeyboardButton(text="Рейтинг", callback_data="edit_field:rating")],
            [InlineKeyboardButton(text="Задачи", callback_data="edit_field:cases")],
            [InlineKeyboardButton(text="⬅️ К списку", callback_data="admin_edit_tool")],
        ]
    )


def get_edit_field_prompt(field: str, tool) -> str:
    prompts = {
        "name": f"Введите новое название.\n\nСейчас: {tool['name']}",
        "description": f"Введите новое описание.\n\nСейчас: {tool['description']}",
        "link": f"Введите новую ссылку.\n\nСейчас: {tool['link']}",
        "image": (
            "Введите новую ссылку на изображение или -, чтобы убрать изображение.\n\n"
            f"Сейчас: {tool['image'] or '-'}"
        ),
        "category": (
            "Введите ключи категорий через запятую.\n\n"
            f"Сейчас: {', '.join(get_tool_category_keys(tool['tool_id'])) or '-'}\n\n"
            f"{get_category_keys_prompt()}"
        ),
        "rating": "Введите новый рейтинг числом, например 4.8.",
        "cases": (
            "Введите ключи задач через запятую или -, чтобы очистить задачи.\n\n"
            f"Сейчас: {', '.join(get_tool_use_case_keys(tool['tool_id'])) or '-'}\n\n"
            f"{get_use_cases_prompt()}"
        ),
    }
    return prompts[field]


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    await state.clear()
    await message.answer(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )


@router.message(F.text == "🛠 Админ-панель")
async def admin_panel_button(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_manage_categories")
async def manage_categories_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Управление категориями каталога:",
        reply_markup=get_category_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_category_add")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Введите ключ новой категории латиницей, например `images` или `productivity_tools`.",
        parse_mode="Markdown",
        reply_markup=get_category_admin_keyboard(),
    )
    await state.set_state(CategoryAdminState.waiting_for_category_key)
    await callback.answer()


@router.callback_query(F.data == "admin_category_rename")
async def rename_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Выберите категорию для переименования:",
        reply_markup=get_category_action_keyboard("admin_category_rename_select"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_rename_select:"))
async def rename_category_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    category_key = callback.data.replace("admin_category_rename_select:", "", 1)
    categories = get_categories()
    category = categories.get(category_key)

    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    await state.update_data(category_key=category_key)
    await callback.message.edit_text(
        f"Введите новое название для категории.\n\nСейчас: {category['title']}",
        reply_markup=get_category_action_keyboard("admin_category_rename_select"),
    )
    await state.set_state(CategoryAdminState.waiting_for_new_category_title)
    await callback.answer()


@router.callback_query(F.data == "admin_category_delete")
async def delete_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Выберите категорию для удаления. Непустую категорию удалить нельзя.",
        reply_markup=get_category_action_keyboard("admin_category_delete_select"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_category_delete_select:"))
async def delete_category_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    category_key = callback.data.replace("admin_category_delete_select:", "", 1)
    categories = get_categories()
    category = categories.get(category_key)

    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    deleted, tools_count = delete_category(category_key)
    if not deleted:
        await callback.answer(
            f"В категории ещё есть нейросети: {tools_count}. Сначала перенесите или удалите их.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"Категория удалена: {category['title']}",
        reply_markup=get_category_admin_keyboard(),
    )
    await callback.answer("Удалено")


@router.message(CategoryAdminState.waiting_for_category_key)
async def save_new_category_key(message: Message, state: FSMContext):
    category_key = (message.text or "").strip().lower()

    if not re.fullmatch(r"[a-z0-9_]+", category_key):
        await message.answer(
            "Ключ категории должен содержать только латинские буквы, цифры и `_`.",
            reply_markup=get_category_admin_keyboard(),
        )
        return

    if category_exists(category_key):
        await message.answer(
            "Категория с таким ключом уже существует. Введите другой ключ.",
            reply_markup=get_category_admin_keyboard(),
        )
        return

    await state.update_data(category_key=category_key)
    await message.answer(
        "Теперь введите название категории, которое увидят пользователи.",
        reply_markup=get_category_admin_keyboard(),
    )
    await state.set_state(CategoryAdminState.waiting_for_category_title)


@router.message(CategoryAdminState.waiting_for_category_title)
async def save_new_category_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    data = await state.get_data()
    category_key = data.get("category_key")

    if not category_key:
        await message.answer("Не удалось определить ключ категории.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    if not title:
        await message.answer(
            "Название категории не должно быть пустым.",
            reply_markup=get_category_admin_keyboard(),
        )
        return

    add_category(category_key, title)
    await message.answer(
        f"Категория добавлена: {title} (`{category_key}`)",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(),
    )
    await state.clear()


@router.message(CategoryAdminState.waiting_for_new_category_title)
async def save_renamed_category_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    data = await state.get_data()
    category_key = data.get("category_key")

    if not category_key:
        await message.answer("Не удалось определить категорию для переименования.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    if not title:
        await message.answer(
            "Название категории не должно быть пустым.",
            reply_markup=get_category_admin_keyboard(),
        )
        return

    updated = update_category_title(category_key, title)
    if not updated:
        await message.answer("Не удалось переименовать категорию.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    tools_count = count_tools_in_category(category_key)
    await message.answer(
        f"Категория обновлена: {title}\nНейросетей в категории: {tools_count}",
        reply_markup=get_admin_keyboard(),
    )
    await state.clear()

@router.callback_query(F.data == "admin_edit_tool")
async def edit_tool_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Выберите нейросеть для редактирования:",
        reply_markup=get_edit_tools_keyboard(),
    )
    await state.set_state(EditTool.choose_tool)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_tool:"))
async def select_tool(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    tool_id = callback.data.replace("edit_tool:", "", 1)
    tool = get_tool_by_id(tool_id)

    if not tool:
        await callback.answer("Нейросеть не найдена", show_alert=True)
        return

    await state.update_data(tool_id=tool_id)
    await callback.message.edit_text(
        f"Вы выбрали: {tool['name']}\n\nЧто хотите изменить?",
        reply_markup=get_edit_fields_keyboard(),
    )
    await state.set_state(EditTool.choose_field)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def choose_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    field = callback.data.replace("edit_field:", "", 1)
    allowed_fields = {"name", "description", "link", "image", "category", "rating", "cases"}
    if field not in allowed_fields:
        await callback.answer("Неизвестное поле для редактирования", show_alert=True)
        return

    data = await state.get_data()
    tool_id = data.get("tool_id")
    tool = get_tool_by_id(tool_id) if tool_id else None

    if not tool:
        await callback.answer("Сначала выберите нейросеть", show_alert=True)
        return

    await state.update_data(field=field)
    await callback.message.edit_text(
        get_edit_field_prompt(field, tool),
        reply_markup=get_edit_fields_keyboard(),
    )
    await state.set_state(EditTool.new_value)
    await callback.answer()


@router.message(EditTool.new_value)
async def save_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    tool_id = data.get("tool_id")
    field = data.get("field")

    if not tool_id or not field:
        await message.answer("Не удалось определить, что именно редактировать.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    raw_value = (message.text or "").strip()

    if field == "rating":
        try:
            rating = float(raw_value)
        except ValueError:
            await message.answer("Введите рейтинг числом, например 4.8")
            return

        save_tool_rating(tool_id, rating)
    elif field == "cases":
        case_keys = []
        if raw_value not in {"", "-", "нет", "Нет", "no", "No"}:
            case_keys = [item.strip() for item in raw_value.split(",") if item.strip()]

        available_cases = {case["case_key"] for case in get_use_cases()}
        invalid_case_keys = [case_key for case_key in case_keys if case_key not in available_cases]

        if invalid_case_keys:
            tool = get_tool_by_id(tool_id)
            await message.answer(
                "Не нашёл такие ключи задач: "
                + ", ".join(invalid_case_keys)
                + "\n\n"
                + get_edit_field_prompt("cases", tool),
                reply_markup=get_edit_fields_keyboard(),
            )
            return

        save_tool_use_cases(tool_id, case_keys)
    elif field == "category":
        category_keys = [item.strip() for item in raw_value.split(",") if item.strip()]
        available_categories = set(get_categories().keys())
        invalid_category_keys = [category_key for category_key in category_keys if category_key not in available_categories]

        if not category_keys:
            tool = get_tool_by_id(tool_id)
            await message.answer(
                "Укажите хотя бы одну категорию.\n\n" + get_edit_field_prompt("category", tool),
                reply_markup=get_edit_fields_keyboard(),
            )
            return

        if invalid_category_keys:
            tool = get_tool_by_id(tool_id)
            await message.answer(
                "Не нашёл такие категории: "
                + ", ".join(invalid_category_keys)
                + "\n\n"
                + get_edit_field_prompt("category", tool),
                reply_markup=get_edit_fields_keyboard(),
            )
            return

        save_tool_categories(tool_id, category_keys)
    else:
        value = None if field == "image" and raw_value in {"", "-", "нет", "Нет", "no", "No"} else raw_value
        updated = update_tool_field(tool_id, field, value)

        if not updated:
            await message.answer("Не удалось обновить нейросеть.", reply_markup=get_admin_keyboard())
            await state.clear()
            return

    tool = get_tool_by_id(tool_id)
    await message.answer(
        f"Значение обновлено для {tool['name']}.",
        reply_markup=get_admin_keyboard(),
    )
    await state.clear()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    users = get_users_count()
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: {users}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 Отправьте сообщение для рассылки.",
        reply_markup=get_broadcast_cancel_keyboard(),
    )
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_broadcast")
async def admin_cancel_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Рассылка отменена.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer("Отменено")


@router.callback_query(F.data == "admin_delete_tool")
async def admin_delete_tool_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите категорию для удаления нейросети:",
        reply_markup=get_admin_categories_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_cat:"))
async def admin_delete_tool_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    category_key = callback.data.replace("admin_del_cat:", "", 1)
    categories = get_categories()
    category = categories.get(category_key)

    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    if not category.get("tools"):
        await callback.answer("В этой категории нет нейросетей", show_alert=True)
        return

    await callback.message.edit_text(
        f"Категория: {category['title']}\n\nВыберите нейросеть для удаления:",
        reply_markup=get_admin_tools_keyboard(category_key),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_del_tool:"))
async def admin_delete_tool_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    tool_id = callback.data.replace("admin_del_tool:", "", 1)
    deleted_name = delete_tool(tool_id)

    if not deleted_name:
        await callback.answer("Нейросеть не найдена", show_alert=True)
        return

    await callback.message.edit_text(
        f"Нейросеть удалена: {deleted_name}",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer("Удалено")


@router.callback_query(F.data == "admin_add_tool")
async def add_tool_start_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "Введите название нейросети",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.name)
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_add_tool")
async def cancel_add_tool_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "Добавление нейросети отменено.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer("Отменено")


@router.callback_query(F.data == "admin_update_rating")
async def choose_tool_for_rating(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите нейросеть для обновления рейтинга:",
        reply_markup=get_rating_tools_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_ban_user")
async def admin_ban_user_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.update_data(moderation_action="ban")
    await callback.message.edit_text(
        "Введите ID пользователя для бана:",
        reply_markup=get_user_moderation_back_keyboard(),
    )
    await state.set_state(UserModerationState.waiting_for_user_id)
    await callback.answer()


@router.callback_query(F.data == "admin_unban_user")
async def admin_unban_user_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.update_data(moderation_action="unban")
    await callback.message.edit_text(
        "Введите ID пользователя для разбана:",
        reply_markup=get_user_moderation_back_keyboard(),
    )
    await state.set_state(UserModerationState.waiting_for_user_id)
    await callback.answer()


@router.callback_query(F.data.startswith("rating_tool:"))
async def select_tool_for_rating(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    tool_id = callback.data.replace("rating_tool:", "", 1)
    await state.update_data(tool_id=tool_id)

    await callback.message.delete()
    await callback.message.answer(
        "Введите новый рейтинг нейросети:",
        reply_markup=get_rating_back_keyboard(),
    )
    await state.set_state(RatingState.waiting_for_rating)
    await callback.answer()


@router.message(RatingState.waiting_for_rating, F.text == "📚 Каталог нейросетей")
async def exit_rating_to_catalog(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CatalogStates.catalog_menu)
    await message.answer(
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard(),
    )


@router.message(RatingState.waiting_for_rating)
async def save_rating(message: Message, state: FSMContext):
    try:
        rating = float(message.text)
    except ValueError:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    tool_id = data.get("tool_id")
    if not tool_id:
        await message.answer("Не удалось определить нейросеть для обновления рейтинга.")
        await state.clear()
        return

    save_tool_rating(tool_id, rating)
    await message.answer("⭐ Рейтинг обновлен", reply_markup=get_admin_keyboard())
    await state.clear()


@router.message(UserModerationState.waiting_for_user_id)
async def process_user_moderation(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except ValueError:
        await message.answer("Введите корректный числовой ID пользователя.")
        return

    data = await state.get_data()
    action = data.get("moderation_action")

    if action == "ban":
        updated = ban_user(user_id)
        result_text = "Пользователь забанен." if updated else "Пользователь не найден."
    elif action == "unban":
        updated = unban_user(user_id)
        result_text = "Пользователь разбанен." if updated else "Пользователь не найден."
    else:
        result_text = "Не удалось определить действие."

    await message.answer(result_text, reply_markup=get_admin_keyboard())
    await state.clear()


@router.message(F.text == "➕ Добавить нейросеть")
async def add_tool_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите название нейросети",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.name)


@router.message(AddTool.name)
async def add_tool_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Введите описание",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.description)


@router.message(AddTool.description)
async def add_tool_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Введите ссылку",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.link)


@router.message(AddTool.link)
async def add_tool_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer(
        "Введите прямую ссылку на изображение или напишите '-'",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.image)


@router.message(AddTool.image)
async def add_tool_image(message: Message, state: FSMContext):
    image = message.text.strip() if message.text else ""
    if image in {"-", "нет", "Нет", "no", "No"}:
        image = None

    await state.update_data(image=image)
    await message.answer(
        get_category_keys_prompt(),
        parse_mode="Markdown",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.category)


@router.message(AddTool.category)
async def add_tool_category(message: Message, state: FSMContext):
    raw_value = (message.text or "").strip()
    category_keys = [item.strip() for item in raw_value.split(",") if item.strip()]
    available_categories = set(get_categories().keys())
    invalid_category_keys = [category_key for category_key in category_keys if category_key not in available_categories]

    if not category_keys:
        await message.answer(
            "Укажите хотя бы одну категорию.\n\n" + get_category_keys_prompt(),
            parse_mode="Markdown",
            reply_markup=get_add_tool_cancel_keyboard(),
        )
        return

    if invalid_category_keys:
        await message.answer(
            "Не нашёл такие категории: "
            + ", ".join(invalid_category_keys)
            + "\n\n"
            + get_category_keys_prompt(),
            parse_mode="Markdown",
            reply_markup=get_add_tool_cancel_keyboard(),
        )
        return

    await state.update_data(category=category_keys)
    await message.answer(
        get_use_cases_prompt(),
        parse_mode="Markdown",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.use_cases)


@router.message(AddTool.use_cases)
async def add_tool_use_cases_step(message: Message, state: FSMContext):
    raw_value = (message.text or "").strip()
    case_keys = []

    if raw_value not in {"", "-", "нет", "Нет", "no", "No"}:
        case_keys = [item.strip() for item in raw_value.split(",") if item.strip()]

    available_cases = {case["case_key"] for case in get_use_cases()}
    invalid_case_keys = [case_key for case_key in case_keys if case_key not in available_cases]

    if invalid_case_keys:
        await message.answer(
            "Не нашёл такие ключи задач: "
            + ", ".join(invalid_case_keys)
            + "\n\n"
            + get_use_cases_prompt(),
            parse_mode="Markdown",
            reply_markup=get_add_tool_cancel_keyboard(),
        )
        return

    data = await state.get_data()
    tool_id = generate_unique_tool_id(data["name"])

    add_tool(
        tool_id,
        data["category"][0],
        data["name"],
        data["description"],
        data["link"],
        data.get("image"),
    )

    save_tool_categories(tool_id, data["category"])

    if case_keys:
        save_tool_use_cases(tool_id, case_keys)

    await message.answer(
        f"Нейросеть добавлена!\nID: `{tool_id}`",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(),
    )
    await state.clear()


@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📢 Отправьте сообщение для рассылки.",
        reply_markup=get_broadcast_cancel_keyboard(),
    )
    await state.set_state(BroadcastState.waiting_for_message)


@router.message(Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("❌ Нет активного действия для отмены.")
        return

    await state.clear()
    await message.answer("✅ Действие отменено.")


@router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    users = get_all_users()

    total = len(users)
    success = 0
    failed = 0

    await message.answer(f"🚀 Начинаю рассылку...\nПолучателей: {total}")

    async def send_message(user_id):
        nonlocal success, failed

        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            success += 1
        except Exception:
            failed += 1

    tasks = []

    for user in users:
        user_id = user[0]
        tasks.append(send_message(user_id))

        if len(tasks) >= 30:
            await asyncio.gather(*tasks)
            tasks = []
            await asyncio.sleep(0.05)

    if tasks:
        await asyncio.gather(*tasks)

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"👥 Всего: {total}\n"
        f"📨 Отправлено: {success}\n"
        f"❌ Ошибок: {failed}"
    )

    await state.clear()


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    users = get_users_count()
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: {users}"
    )
    await message.answer(text, parse_mode="HTML")
