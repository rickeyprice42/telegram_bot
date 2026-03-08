from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from database.models import get_all_users, get_users_count
from states.broadcast_state import BroadcastState
import asyncio

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return

    text = (
        "🔐 <b>Админ-панель</b>\n\n"
        "Доступные команды:\n"
        "📊 /stats — общая статистика\n"
        "📣 /broadcast — рассылка"
    )
    await message.answer(text)

@router.message(F.text == "🛠 Админ-панель")
async def admin_panel_button(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    text = (
        "🔐 <b>Админ-панель</b>\n\n"
        "Доступные команды:\n"
        "📊 /stats — статистика\n"
        "📢 /broadcast — рассылка"
    )

    await message.answer(text)

@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
    "📢 Отправьте сообщение для рассылки.\n\n"
    "Для отмены используйте /cancel"
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
                message_id=message.message_id
            )
            success += 1
        except:
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
    if message.from_user.id not in ADMIN_IDS:
        return

    users = get_users_count()
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: {users}"
    )
    await message.answer(text)
