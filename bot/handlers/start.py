from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard
from bot.services.dialogue import start_new_topic
from bot.services.tts import synthesize_voice
from bot.states import Conversation

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    name = message.from_user.first_name or "there"

    await message.answer(
        f"Hi, {name}! 👋 Я — твой собеседник для практики английского.\n\n"
        f"Отвечай голосовыми сообщениями, я буду разбирать ошибки "
        f"и оценивать произношение.\n\n"
        f"Кнопка «Меню» — сменить тему разговора в любой момент.",
        reply_markup=main_menu_keyboard(),
    )

    # Тема по умолчанию при первом запуске — 'daily_life', пользователь может
    # сразу сменить через "Меню".
    opening_line = await start_new_topic(message.from_user.id, "daily_life")

    voice_path = await synthesize_voice(opening_line)
    voice_file = voice_path.open("rb")
    try:
        await message.answer_voice(voice=voice_file)
    finally:
        voice_file.close()
        voice_path.unlink(missing_ok=True)

    await state.set_state(Conversation.awaiting_reply)


@router.message(F.text == "💡 Помощь")
async def show_help(message: Message) -> None:
    await message.answer(
        "❓ Не знаешь, что ответить — просто скажи об этом голосом, я подскажу.\n"
        "🎙 Отвечай голосовым сообщением на мой вопрос.\n"
        "🔀 Хочешь сменить тему — нажми «Меню»."
    )


@router.message(F.text == "🏁 Завершить")
async def finish_session(message: Message, state: FSMContext) -> None:
    await state.set_state(Conversation.idle)
    await message.answer("Сессия завершена. Отправь /start, когда будешь готов продолжить 👋")
