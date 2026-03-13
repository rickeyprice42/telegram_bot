from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.picker_kb import picker_menu
from utils.ai_picker import get_tools_for_case

router = Router()


@router.message(F.text == "🤖 Подобрать нейросеть")
async def open_picker(message: Message):
    await message.answer(
        "🧠 Подобрать нейросеть\n\nЧто вы хотите сделать?",
        reply_markup=picker_menu(),
    )


@router.callback_query(F.data.startswith("pick_"))
async def show_tools(callback: CallbackQuery):
    case_key = callback.data.replace("pick_", "", 1)
    tools = get_tools_for_case(case_key)

    if not tools:
        await callback.message.edit_text(
            "Пока нет нейросетей для этой задачи."
        )
        await callback.answer()
        return

    text = "🤖 Подходящие нейросети:\n\n"

    for name, description, link in tools[:5]:
        text += f"• {name}\n{description}\n{link}\n\n"

    await callback.message.edit_text(text)
    await callback.answer()
