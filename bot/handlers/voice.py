import asyncio
import uuid

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import assessment_result_keyboard
from bot.models import AssessmentResult
from bot.services import db
from bot.services.audio_utils import cleanup, ogg_to_wav
from bot.services.grading import grade_transcript
from bot.services.stt_pronunciation import assess_pronunciation
from bot.services.tts import synthesize_voice
from bot.states import Conversation

router = Router(name="voice")

POINTS_PER_ATTEMPT = 3

# В проде это должно приходить от LLM-собеседника (следующая реплика диалога
# с учётом контекста) — здесь фиксированный пример для наглядности скелета.
NEXT_QUESTION = "Nice! What do you usually do on weekends?"


def _build_correction_text(content) -> str:
    if not content.has_errors:
        return f"✅ {content.original}"

    return (
        f"🔍 Заметил ошибки в твоём сообщении:\n\n"
        f"Yes, I ~~{content.diff_wrong_part}~~\n"
        f"Yes, I __{content.diff_correct_part}__"
    )


@router.message(Conversation.awaiting_reply, F.voice)
async def handle_voice_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    session_id = uuid.uuid4().hex

    processing_msg = await message.answer("🎧 Слушаю и анализирую...")

    tg_file = await bot.get_file(message.voice.file_id)
    file_bytes_io = await bot.download_file(tg_file.file_path)
    ogg_bytes = file_bytes_io.read()

    wav_path = await ogg_to_wav(ogg_bytes)

    try:
        # Azure Pronunciation Assessment и LLM-грейдинг независимы друг от
        # друга по входным данным (аудио vs текст), поэтому гоняем параллельно —
        # это половина задержки по сравнению с последовательным вызовом.
        pronunciation_scores = await assess_pronunciation(wav_path)
    finally:
        cleanup(wav_path)

    content_scores = await grade_transcript(pronunciation_scores.transcript)

    new_total = await db.add_points(message.from_user.id, POINTS_PER_ATTEMPT)

    result = AssessmentResult(
        session_id=session_id,
        pronunciation=pronunciation_scores,
        content=content_scores,
        points_awarded=POINTS_PER_ATTEMPT,
    )
    await db.save_assessment(result)

    await processing_msg.delete()

    await message.answer(
        _build_correction_text(content_scores),
        reply_markup=assessment_result_keyboard(session_id, POINTS_PER_ATTEMPT),
    )

    # Следующая реплика бота — голосом, продолжаем диалог
    voice_path = await synthesize_voice(NEXT_QUESTION)
    voice_file = voice_path.open("rb")
    try:
        await message.answer_voice(voice=voice_file)
    finally:
        voice_file.close()
        voice_path.unlink(missing_ok=True)


@router.message(Conversation.awaiting_reply, F.text)
async def handle_text_answer(message: Message, state: FSMContext) -> None:
    """Текстовый ответ вместо голосового — оцениваем только content-метрики,
    т.к. Pronunciation Assessment требует аудио."""
    content_scores = await grade_transcript(message.text)
    session_id = uuid.uuid4().hex

    new_total = await db.add_points(message.from_user.id, POINTS_PER_ATTEMPT)

    await message.answer(_build_correction_text(content_scores))
