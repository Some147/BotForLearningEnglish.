CREATE TABLE IF NOT EXISTS assessments (
    session_id      TEXT PRIMARY KEY,
    pronunciation   JSONB NOT NULL,
    content         JSONB NOT NULL,
    points_awarded  INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_points (
    user_id       BIGINT PRIMARY KEY,
    total_points  INTEGER NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments (created_at);

-- История текущей диалоговой сессии пользователя. Одна активная сессия
-- на пользователя: новая тема из "Меню" сбрасывает историю (см. reset_session).
CREATE TABLE IF NOT EXISTS conversation_sessions (
    user_id     BIGINT PRIMARY KEY,
    topic       TEXT NOT NULL DEFAULT 'general',
    history     JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
