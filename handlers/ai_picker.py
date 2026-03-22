from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards.picker_kb import (
    get_picker_level_keyboard,
    get_picker_preference_keyboard,
    get_picker_result_keyboard,
    picker_menu,
)
from utils.ai_picker import LEVEL_TAGS, PREFERENCE_TAGS, get_tools_for_case, get_use_case_by_key

router = Router()


@router.message(F.text == "🤖 Подобрать нейросеть")
async def open_picker(message: Message):
    await message.answer(
        "🧠 Подобрать нейросеть\n\nВыберите задачу, а потом ответьте на 2 коротких вопроса.",
        reply_markup=picker_menu(),
    )


@router.callback_query(F.data == "picker_back")
async def picker_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🧠 Подобрать нейросеть\n\nВыберите задачу, а потом ответьте на 2 коротких вопроса.",
        reply_markup=picker_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pick_case:"))
async def pick_case(callback: CallbackQuery):
    case_key = callback.data.replace("pick_case:", "", 1)
    use_case = get_use_case_by_key(case_key)

    if not use_case:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    title = use_case["title"]
    await callback.message.edit_text(
        f"🧠 Подобрать нейросеть\n\nЗадача: {title}\n\n1. Какой тип нейросети нужен?",
        reply_markup=get_picker_level_keyboard(case_key),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pick_level:"))
async def pick_level(callback: CallbackQuery):
    _, case_key, level_tag = callback.data.split(":", 2)
    use_case = get_use_case_by_key(case_key)

    if not use_case:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    title = use_case["title"]
    level_title = LEVEL_TAGS.get(level_tag, level_tag)
    await callback.message.edit_text(
        f"🧠 Подобрать нейросеть\n\nЗадача: {title}\nТип: {level_title}\n\n2. Что для вас важнее?",
        reply_markup=get_picker_preference_keyboard(case_key, level_tag),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pick_pref:"))
async def pick_preference(callback: CallbackQuery):
    _, case_key, level_tag, preference_tag = callback.data.split(":", 3)
    use_case = get_use_case_by_key(case_key)

    if not use_case:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    tools = [dict(tool) for tool in get_tools_for_case(case_key, level_tag, preference_tag)][:3]
    if not tools:
        await callback.message.edit_text(
            "Пока нет нейросетей для этой задачи.",
            reply_markup=get_picker_result_keyboard(case_key),
        )
        await callback.answer()
        return

    title = use_case["title"]
    level_title = LEVEL_TAGS.get(level_tag, level_tag)
    preference_title = PREFERENCE_TAGS.get(preference_tag, preference_tag)

    text = (
        "🤖 Подходящие нейросети\n\n"
        f"Задача: {title}\n"
        f"Тип: {level_title}\n"
        f"Приоритет: {preference_title}\n\n"
    )

    best_match_score = tools[0]["match_score"] if tools else 0
    if best_match_score <= 0:
        text += "Точных совпадений по меткам пока нет, поэтому показываю лучшие варианты по задаче.\n\n"

    for tool in tools:
        text += (
            f"• {tool['name']}\n"
            f"{tool['description']}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_picker_result_keyboard(case_key, tools),
    )
    await callback.answer()
