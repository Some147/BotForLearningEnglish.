from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard
from bot.services.tts import synthesize_voice
from bot.states import Conversation

router = Router(name="start")

OPENING_LINE = (
    "Hey! I'm your English speaking partner. "
    "Let's start — how are you doing today?"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    name = message.from_user.first_name or "there"

    await message.answer(
        f"Hi, {name}! 👋 Я — твой собеседник для практики английского.\n\n"
        f"Отвечай голосовыми сообщениями, я буду разбирать ошибки "
        f"и оценивать произношение.",
        reply_markup=main_menu_keyboard(),
    )

    voice_path = await synthesize_voice(OPENING_LINE)
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
        "🔄 Хочешь сменить тему — нажми «Завершить» и начни заново."
    )


@router.message(F.text == "🏁 Завершить")
async def finish_session(message: Message, state: FSMContext) -> None:
    await state.set_state(Conversation.idle)
    await message.answer("Сессия завершена. Отправь /start, когда будешь готов продолжить 👋")
