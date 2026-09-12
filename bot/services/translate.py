"""
Перевод отдельных слов и целых фраз для Mini App экрана "Текст".

Решение сделать это через LLM, а не через отдельный словарный API
(Yandex Dictionary / DeepL) — сознательный компромисс: один вендор
(Anthropic) вместо трёх (Azure + Anthropic + словарь), меньше ключей
и меньше точек отказа. Для продакшена с высокой нагрузкой имеет смысл
пересчитать экономику — словарный API дешевле на коротких словах,
но требует отдельного контракта и ключа.
"""

import json

from anthropic import AsyncAnthropic

from bot.config import settings

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Ты — англо-русский переводчик для приложения изучения языка.
Тебе дают либо одно слово с контекстом (полным предложением), либо целую фразу.

Верни СТРОГО валидный JSON без markdown:
{
  "translation": "перевод на русский",
  "transcription": "транскрипция IPA, только если input - одно слово, иначе null"
}"""


async def translate_word(word: str, context_sentence: str) -> dict:
    prompt = f'Слово: "{word}"\nКонтекст (предложение целиком): "{context_sentence}"'
    return await _translate(prompt)


async def translate_phrase(phrase: str) -> dict:
    prompt = f'Фраза целиком: "{phrase}"'
    return await _translate(prompt)


async def _translate(user_prompt: str) -> dict:
    response = await _client.messages.create(
        model=settings.llm_model,
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)
