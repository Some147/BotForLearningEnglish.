from aiogram.fsm.state import State, StatesGroup


class Conversation(StatesGroup):
    """Состояния голосового диалога с ботом."""

    idle = State()          # пользователь ещё не начал сессию
    awaiting_reply = State()  # бот задал вопрос, ждём voice/текст ответ
    session_active = State()  # сессия идёт, между репликами
