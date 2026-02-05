from pydantic import BaseModel

from app.page_handler.data_parser.models import AlbumInformation, AlbumSearch


class AlbumInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    album_info: AlbumInformation | None = None
    error: str | None = None
    url: str
    processing_time: float

class SearchResponse(BaseModel):
    """Модель ответа поиска группы"""
    success: bool
    results: list[AlbumSearch] | None = None
    error: str | None = None
    url: str
    processing_time: float
