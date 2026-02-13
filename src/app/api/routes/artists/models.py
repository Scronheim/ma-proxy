from pydantic import BaseModel

from app.page_handler.data_parser.models import Member

class MemberInfoResponse(BaseModel):
    """Модель ответа с информацией об участнике"""
    success: bool
    data: Member | None = None
    error: str | None = None
    url: str
    processing_time: float
