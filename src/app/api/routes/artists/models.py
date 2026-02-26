from pydantic import BaseModel

from app.page_handler.data_parser.models import Member, RipArtistsResults

class MemberInfoResponse(BaseModel):
    """Модель ответа с информацией об участнике"""
    success: bool
    data: Member | None = None
    error: str | None = None
    url: str
    processing_time: float

class RipMembersInfoResponse(BaseModel):
    """Модель ответа с информацией об умерших музыкантах"""
    success: bool
    data: RipArtistsResults | None = None
    error: str | None = None
    url: str
    processing_time: float
