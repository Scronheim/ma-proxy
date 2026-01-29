from pydantic import BaseModel

from app.page_handler.data_parser.models import AlbumInformation


class AlbumInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    album_info: AlbumInformation | None = None
    error: str | None = None
    url: str
    processing_time: float
