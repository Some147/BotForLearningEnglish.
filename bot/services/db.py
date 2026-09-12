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
