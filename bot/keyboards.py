from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.config import settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔀 Меню"), KeyboardButton(text="💡 Помощь")],
            [KeyboardButton(text="🏁 Завершить")],
        ],
        resize_keyboard=True,
    )


def topics_keyboard() -> InlineKeyboardMarkup:
    """Выбор темы разговора — открывается по кнопке 'Меню'."""
    from bot.services.dialogue import TOPICS

    labels = {
        "travel": "✈️ Путешествия",
        "job_interview": "💼 Собеседование",
        "daily_life": "☕️ Повседневная жизнь",
        "business": "📈 Бизнес",
        "random": "🎲 Случайная тема",
    }
    rows = [
        [InlineKeyboardButton(text=labels[key], callback_data=f"topic:{key}")]
        for key in TOPICS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def assessment_result_keyboard(session_id: str, points_awarded: int) -> InlineKeyboardMarkup:
    """Кнопки под voice-ответом бота с оценкой: Объяснение ошибок / Оценка произношения."""
    correction_url = f"{settings.webapp_base_url}/correction/{session_id}"
    pronunciation_url = f"{settings.webapp_base_url}/pronunciation/{session_id}"
    transcript_url = f"{settings.webapp_base_url}/transcript/{session_id}"

    rows = [
        [
            InlineKeyboardButton(
                text="📖 Объяснение ошибок",
                web_app=WebAppInfo(url=correction_url),
            )
        ],
        [
            InlineKeyboardButton(
                text="🗣 Оценка произношения",
                web_app=WebAppInfo(url=pronunciation_url),
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Текст",
                web_app=WebAppInfo(url=transcript_url),
            ),
            InlineKeyboardButton(text=f"⭐ +{points_awarded}", callback_data="noop"),
        ],
        [
            InlineKeyboardButton(text="💡 Помощь", callback_data="help"),
            InlineKeyboardButton(text="🏁 Завершить", callback_data="finish"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
