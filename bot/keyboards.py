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
            [KeyboardButton(text="💡 Помощь"), KeyboardButton(text="🏁 Завершить")],
        ],
        resize_keyboard=True,
    )


def assessment_result_keyboard(session_id: str, points_awarded: int) -> InlineKeyboardMarkup:
    """Кнопки под voice-ответом бота с оценкой: Объяснение ошибок / Оценка произношения."""
    correction_url = f"{settings.webapp_base_url}/correction/{session_id}"
    pronunciation_url = f"{settings.webapp_base_url}/pronunciation/{session_id}"

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
            InlineKeyboardButton(text="💬 Текст", callback_data="show_text"),
            InlineKeyboardButton(text=f"⭐ +{points_awarded}", callback_data="noop"),
        ],
        [
            InlineKeyboardButton(text="💡 Помощь", callback_data="help"),
            InlineKeyboardButton(text="🏁 Завершить", callback_data="finish"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
