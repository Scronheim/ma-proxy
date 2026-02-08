from pydantic import BaseModel

from app.page_handler.data_parser.models import BandInformation, BandSearch, BandLink, RandomBandInfo


class BandInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    data: BandInformation | None = None
    error: str | None = None
    url: str
    processing_time: float

class RandomBandIdResponse(BaseModel):
    """Модель ответа с информацией о случайном ID группы"""
    success: bool
    data: RandomBandInfo | None = None
    error: str | None = None
    url: str
    processing_time: float

class BandLinksResponse(BaseModel):
    """Модель ответа с информацией о ссылках группы"""
    success: bool
    data: list[BandLink] | None = None
    error: str | None = None
    url: str
    processing_time: float

class SearchResponse(BaseModel):
    """Модель ответа поиска группы"""
    success: bool
    data: list[BandSearch] | None = None
    error: str | None = None
    url: str
    processing_time: float
