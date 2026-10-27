from pydantic import BaseModel

from app.page_handler.data_parser.models import UpcomingReleasesResults


class UpcomingReleasesInfoResponse(BaseModel):
    """Модель ответа с информацией предстоящих релизах"""
    success: bool
    data: UpcomingReleasesResults | None = None
    error: str | None = None
    url: str
    processing_time: float
