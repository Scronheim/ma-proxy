from pydantic import BaseModel

class SongInfoResponse(BaseModel):
    """Модель ответа с информацией о треке"""
    success: bool
    data: str | None = None
    error: str | None = None
    url: str
    processing_time: float
