from dataclasses import dataclass


@dataclass
class PageInfo:
    url: str
    processing_time: float
    error: str | None = None
    data: dict | None = None
    html: str | None = None
