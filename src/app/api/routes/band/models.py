from pydantic import BaseModel

from app.page_handler.data_parser.models import BandInformation, BandSearch


class BandInfoResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    success: bool
    band_info: BandInformation | None = None
    error: str | None = None
    url: str
    processing_time: float

class BandSearchResponse(BaseModel):
    """Модель ответа поиска группы"""
    success: bool
    bands: list[BandSearch] | None = None
    error: str | None = None
    url: str
    processing_time: float
