from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import topics_keyboard
from bot.services.dialogue import start_new_topic
from bot.services.tts import synthesize_voice
from bot.states import Conversation

router = Router(name="menu")


@router.message(F.text == "🔀 Меню")
async def show_topics(message: Message) -> None:
    await message.answer(
        "О чём хочешь поговорить сегодня?",
        reply_markup=topics_keyboard(),
    )


@router.callback_query(F.data.startswith("topic:"))
async def select_topic(callback: CallbackQuery, state: FSMContext) -> None:
    topic = callback.data.removeprefix("topic:")

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    opening_line = await start_new_topic(callback.from_user.id, topic)

    voice_path = await synthesize_voice(opening_line)
    voice_file = voice_path.open("rb")
    try:
        await callback.message.answer_voice(voice=voice_file)
    finally:
        voice_file.close()
        voice_path.unlink(missing_ok=True)

    await state.set_state(Conversation.awaiting_reply)
