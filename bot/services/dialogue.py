"""
Диалоговый движок — генерирует реплики бота-собеседника с учётом выбранной
темы и истории разговора. Заменяет захардкоженные OPENING_LINE/NEXT_QUESTION
из первой версии скелета.
"""

from anthropic import AsyncAnthropic

from bot.config import settings
from bot.services import db

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

TOPICS = {
    "travel": "Travel and trips abroad",
    "job_interview": "Job interview practice",
    "daily_life": "Daily life and small talk",
    "business": "Business and work discussions",
    "random": "Any topic — surprise the student",
}

SYSTEM_PROMPT_TEMPLATE = """Ты — дружелюбный AI-собеседник по имени Alex для практики
разговорного английского. Тема текущего разговора: {topic_description}.

Правила:
- Общайся ТОЛЬКО на английском, независимо от языка сообщений студента.
- Задавай один открытый вопрос за реплику — не перегружай студента.
- Реагируй на то, что студент сказал, прежде чем задать следующий вопрос
  (естественный small talk, а не допрос).
- Длина реплики — 1-3 коротких предложения, разговорный стиль.
- Не исправляй ошибки студента здесь — этим занимается отдельная система
  оценки, твоя роль — только поддерживать диалог.
- Никогда не выходи из роли и не упоминай, что ты языковая модель."""


async def generate_reply(topic: str, history: list[dict]) -> str:
    """Генерирует следующую реплику бота с учётом темы и истории диалога.

    history — список {"role": "user"|"assistant", "content": str}, уже
    ограниченный по длине на уровне db.append_to_history.
    """
    topic_description = TOPICS.get(topic, TOPICS["random"])
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(topic_description=topic_description)

    messages = history if history else [
        {"role": "user", "content": "[Начни разговор первым, поприветствуй студента]"}
    ]

    response = await _client.messages.create(
        model=settings.llm_model,
        max_tokens=150,
        system=system_prompt,
        messages=messages,
    )

    return "".join(block.text for block in response.content if block.type == "text").strip()


async def start_new_topic(user_id: int, topic: str) -> str:
    """Сбрасывает сессию под новую тему и возвращает первую реплику бота."""
    await db.reset_session(user_id, topic)
    opening_line = await generate_reply(topic, history=[])
    await db.append_to_history(user_id, "assistant", opening_line)
    return opening_line


async def continue_dialogue(user_id: int, user_transcript: str) -> str:
    """Добавляет ответ студента в историю и возвращает следующую реплику бота."""
    session = await db.get_session(user_id)
    history = await db.append_to_history(user_id, "user", user_transcript)

    reply = await generate_reply(session["topic"], history)
    await db.append_to_history(user_id, "assistant", reply)
    return reply
