from pydantic import BaseModel

from app.page_handler.data_parser.models import BandInformation, BandSearch, BandLink


class BandInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    band_info: BandInformation | None = None
    error: str | None = None
    url: str
    processing_time: float

class BandLinksResponse(BaseModel):
    """Модель ответа с информацией о ссылках группы"""
    success: bool
    band_links: list[BandLink] | None = None
    error: str | None = None
    url: str
    processing_time: float

class SearchResponse(BaseModel):
    """Модель ответа поиска группы"""
    success: bool
    results: list[BandSearch] | None = None
    error: str | None = None
    url: str
    processing_time: float
