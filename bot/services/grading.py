"""
Content-оценка речи (Grammar, Vocabulary) + генерация diff "было/стало"
поверх транскрипта, полученного от Azure Pronunciation Assessment.

Это замена нативному Azure content-assessment, который retired начиная
с Speech SDK 1.46 — Microsoft сама рекомендует считать эти метрики через
LLM (см. официальную документацию по Pronunciation Assessment).
"""

import json

from anthropic import AsyncAnthropic

from bot.config import settings
from bot.models import ContentScores

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Ты — оценщик устной английской речи для приложения-репетитора.
Тебе дают транскрипт голосового ответа студента (может быть неполным или содержать
артефакты распознавания речи).

Верни СТРОГО валидный JSON, без markdown-разметки и пояснений вне JSON, по схеме:
{
  "has_errors": bool,
  "original": "точная фраза студента как есть",
  "corrected": "исправленная фраза, если есть ошибки; иначе = original",
  "diff_wrong_part": "конкретное неверное слово/фраза из original, или null если ошибок нет",
  "diff_correct_part": "конкретное верное слово/фраза для замены, или null если ошибок нет",
  "explanation_ru": "объяснение грамматического правила на русском, 1-2 предложения, или null",
  "grammar_score": int от 0 до 100,
  "vocabulary_score": int от 0 до 100,
  "tip_ru": "короткий персональный совет на русском, 1 предложение, по стилю речи (беглость/интонация/лексика)"
}

Правила:
- Если фраза грамматически корректна, has_errors=false, diff-поля = null.
- grammar_score учитывает только синтаксис и морфологию, НЕ лексику.
- vocabulary_score оценивает разнообразие и уместность выбранных слов относительно уровня.
- diff_wrong_part и diff_correct_part должны быть МИНИМАЛЬНЫМ фрагментом, а не всей фразой
  (например "would" -> "do", а не вся фраза целиком)."""


async def grade_transcript(transcript: str) -> ContentScores:
    response = await _client.messages.create(
        model=settings.llm_model,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Транскрипт студента: {transcript!r}"}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # LLM иногда оборачивает JSON в ```json — на всякий случай подчищаем.
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    data = json.loads(raw_text)

    return ContentScores(
        grammar=data["grammar_score"],
        vocabulary=data["vocabulary_score"],
        has_errors=data["has_errors"],
        original=data["original"],
        corrected=data["corrected"],
        diff_wrong_part=data.get("diff_wrong_part"),
        diff_correct_part=data.get("diff_correct_part"),
        explanation_ru=data.get("explanation_ru"),
        tip_ru=data["tip_ru"],
    )
