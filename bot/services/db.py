import json
from typing import Optional

import asyncpg

from bot.config import settings
from bot.models import AssessmentResult

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    return _pool


async def save_assessment(result: AssessmentResult) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO assessments (session_id, pronunciation, content, points_awarded)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (session_id) DO UPDATE
                SET pronunciation = EXCLUDED.pronunciation,
                    content = EXCLUDED.content,
                    points_awarded = EXCLUDED.points_awarded
            """,
            result.session_id,
            result.pronunciation.model_dump_json(),
            result.content.model_dump_json(),
            result.points_awarded,
        )


async def load_assessment(session_id: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT pronunciation, content, points_awarded FROM assessments WHERE session_id = $1",
            session_id,
        )
    if row is None:
        return None
    return {
        "pronunciation": json.loads(row["pronunciation"]),
        "content": json.loads(row["content"]),
        "points_awarded": row["points_awarded"],
    }


async def get_session(user_id: int) -> dict:
    """Возвращает текущую тему и историю диалога пользователя.
    Если сессии ещё нет — создаёт с темой 'general' и пустой историей."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT topic, history FROM conversation_sessions WHERE user_id = $1",
            user_id,
        )
        if row is None:
            await conn.execute(
                """
                INSERT INTO conversation_sessions (user_id, topic, history)
                VALUES ($1, 'general', '[]'::jsonb)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
            )
            return {"topic": "general", "history": []}

    return {"topic": row["topic"], "history": json.loads(row["history"])}


async def reset_session(user_id: int, topic: str) -> None:
    """Начинает новый диалог с чистой историей под выбранную тему."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversation_sessions (user_id, topic, history, updated_at)
            VALUES ($1, $2, '[]'::jsonb, now())
            ON CONFLICT (user_id) DO UPDATE
                SET topic = EXCLUDED.topic,
                    history = '[]'::jsonb,
                    updated_at = now()
            """,
            user_id,
            topic,
        )


async def append_to_history(user_id: int, role: str, content: str) -> list:
    """Добавляет реплику в историю сессии и возвращает обновлённую историю.

    История хранится целиком в JSONB, а не отдельными строками — для
    диалогового бота нужен весь контекст разом на каждый LLM-вызов,
    отдельная таблица messages добавила бы JOIN без пользы на этом масштабе.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT history FROM conversation_sessions WHERE user_id = $1", user_id
        )
        history = json.loads(row["history"]) if row else []
        history.append({"role": role, "content": content})

        # Ограничиваем окно контекста последними 20 репликами — иначе стоимость
        # токенов на LLM-вызов растёт линейно с длиной разговора без пользы
        # для качества ответа.
        history = history[-20:]

        await conn.execute(
            """
            UPDATE conversation_sessions
                SET history = $2::jsonb, updated_at = now()
                WHERE user_id = $1
            """,
            user_id,
            json.dumps(history),
        )
    return history


async def add_points(user_id: int, points: int) -> int:
    """Начисляет баллы и возвращает новый суммарный баланс."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO user_points (user_id, total_points)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
                SET total_points = user_points.total_points + EXCLUDED.total_points
            RETURNING total_points
            """,
            user_id,
            points,
        )
    return row["total_points"]
