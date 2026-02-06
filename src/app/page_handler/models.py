from dataclasses import dataclass

from app.page_handler.data_parser.models import BandInformation, AlbumInformation


@dataclass
class PageInfo:
    url: str
    processing_time: float
    error: str | None = None
    data: BandInformation | AlbumInformation | None = None
    html: str | None = None
