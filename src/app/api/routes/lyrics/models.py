from pydantic import BaseModel

class LyricsInfoResponse(BaseModel):
    """Модель ответа с информацией о тексте"""
    success: bool
    lyrics: str | None = None
    error: str | None = None
    url: str
    processing_time: float
