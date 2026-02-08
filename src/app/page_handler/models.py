from dataclasses import dataclass

from app.page_handler.data_parser.models import BandInformation, AlbumInformation, BandSearch, StatInfo, BandLink


@dataclass
class PageInfo:
    url: str
    processing_time: float
    error: str | None = None
    html: str | None = None
    data: BandInformation | AlbumInformation | StatInfo | list[BandLink] | None | list[BandSearch] = None

