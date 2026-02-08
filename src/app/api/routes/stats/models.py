from pydantic import BaseModel

from app.page_handler.data_parser.models import AllStatInfo


class StatsInfoResponse(BaseModel):
    """Модель ответа с информацией о статистике"""
    success: bool
    data: AllStatInfo | None = None
    error: str | None = None
    url: str
    processing_time: float
