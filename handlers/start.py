import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config import CHANNEL_ID
from keyboards.menu_keyboard import get_main_menu
from keyboards.subscription_keyboard import subscribe_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> bool | None:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in {"member", "administrator", "creator"}
    except TelegramBadRequest as e:
        # Most common reason: bot is not admin in channel / wrong channel id.
        if "member list is inaccessible" in str(e):
            logger.exception(
                "Subscription check is not available. "
                "Make sure bot is admin in channel %s",
                CHANNEL_ID,
            )
            return None
        raise


@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    subscribed = await check_subscription(bot, user_id)

    if subscribed is None:
        await message.answer(
            "Не удалось проверить подписку.\n"
            "Проверьте, что бот добавлен в канал как администратор."
        )
        return

    if not subscribed:
        await message.answer(
            "📣 Для использования бота подпишитесь на канал Neural Hub.",
            reply_markup=subscribe_keyboard,
        )
        return

    await message.answer(
    f"""🚀 Привет, {message.from_user.first_name}! Добро пожаловать в <b>Neural Hub Bot</b>!

Это каталог лучших нейросетей и AI-инструментов для работы, учебы и творчества.

📚 <b>В боте вы найдете:</b>
• Каталог нейросетей по категориям
• Возможность сохранять AI в избранное
• Подбор нейросети под вашу задачу
• 🔥 Лучшие AI инструменты
• Полезные гайды и промпты

🤖 Neural Hub помогает быстро находить нужные AI-инструменты без долгих поисков в интернете.

Выберите нужный раздел в меню ниже и начните исследовать мир нейросетей.
""",
    parse_mode="HTML",
    reply_markup=get_main_menu(message.from_user.id)
)


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot):
    subscribed = await check_subscription(bot, callback.from_user.id)

    if subscribed is None:
        await callback.answer(
            "Проверка временно недоступна. Сообщите администратору.",
            show_alert=True,
        )
        return

    if not subscribed:
        await callback.answer(
            "Вы еще не подписаны на канал.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        f"Привет, {callback.from_user.first_name}!",
        reply_markup=get_main_menu(callback.from_user.id),
    )
    await callback.answer("Подписка подтверждена ✅")
