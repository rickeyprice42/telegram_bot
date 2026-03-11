import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMIN_IDS
from database.database import add_tool, delete_tool, get_all_tools, save_tool_rating
from database.models import get_all_users, get_users_count
from keyboards.catalog_keyboard import get_catalog_keyboard
from states.admin_states import AddTool, RatingState
from states.broadcast_state import BroadcastState
from states.catalog_states import CatalogStates
from utils.ai_catalog import get_categories

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="❌ Удалить нейросеть", callback_data="admin_delete_tool"),
            ],
            [InlineKeyboardButton(text="➕ Добавить нейросеть", callback_data="admin_add_tool")],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="⭐ Обновить рейтинг AI", callback_data="admin_update_rating"),
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


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    await message.answer(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )


@router.message(F.text == "🛠 Админ-панель")
async def admin_panel_button(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        get_admin_panel_text(),
        parse_mode="HTML",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


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
        "Введите ключ категории",
        reply_markup=get_add_tool_cancel_keyboard(),
    )
    await state.set_state(AddTool.category)


@router.message(AddTool.category)
async def add_tool_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    data = await state.get_data()
    tool_id = data["name"].lower().replace(" ", "_")

    add_tool(
        tool_id,
        message.text,
        data["name"],
        data["description"],
        data["link"],
        data.get("image"),
    )
    await message.answer("Нейросеть добавлена!")
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
