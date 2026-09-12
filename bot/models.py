from pydantic import BaseModel, Field


class PronunciationScores(BaseModel):
    """Акустические метрики из Azure Pronunciation Assessment."""

    accuracy: int = Field(ge=0, le=100)
    fluency: int = Field(ge=0, le=100)
    prosody: int = Field(ge=0, le=100)
    transcript: str


class ContentScores(BaseModel):
    """Текстовые метрики + разбор ошибок, считает LLM поверх транскрипта."""

    grammar: int = Field(ge=0, le=100)
    vocabulary: int = Field(ge=0, le=100)
    has_errors: bool
    original: str
    corrected: str
    diff_wrong_part: str | None = None
    diff_correct_part: str | None = None
    explanation_ru: str | None = None
    tip_ru: str  # короткий совет, e.g. "Работай над интонацией в конце фразы"


class AssessmentResult(BaseModel):
    """Полный результат одной голосовой реплики — то, что уйдёт в Mini App."""

    session_id: str
    pronunciation: PronunciationScores
    content: ContentScores
    points_awarded: int
