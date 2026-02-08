from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BandStatInfo:
    active: int = 0
    on_hold: int = 0
    split_up: int = 0
    changed_name: int = 0
    unknown: int = 0
    total: int = 0

@dataclass
class StatInfo:
    bands: BandStatInfo
    albums: int = 0
    songs: int = 0

@dataclass
class AllStatInfo:
    local: StatInfo
    ma: StatInfo

@dataclass
class BandLocationInfo:
    country: str | None = None
    city: str | None = None

@dataclass
class MemberLineUp:
    name: str | None = None
    role: str | None = None
    url: str | None = None

@dataclass
class Album:
    title: str | None = None
    year: str = "N/A"
    type: str = "N/A"
    id: str | None = None
    url: str | None = None

@dataclass
class StatusAndDateInfo:
    status: str | None = None
    formed_in: str | None = None
    years_active: str | None = None

@dataclass
class Track:
    id: int | str | None = None
    number: int | None = None
    title: str | None = None
    duration: str | None = None
    lyrics: str | None = None
    cdNumber: int | None = None
    side: str | None = None

@dataclass
class AlbumInformation:
    id: int | None = None
    title: str | None = None
    band_name: str | None = None
    band_id: int | None = None
    type: str | None = None
    release_date: str | None = None
    label: str | None = None
    tracklist: list[Track] | None = None
    cover_url: str | None = None
    updated_at: datetime | str | None = None
    parsing_error: str | None = None
    url: str | None = None

@dataclass
class AlbumShortInformation:
    id: int | None = None
    title: str | None = None
    type: str | None = None
    release_date: str | None = None
    cover_url: str | None = None
    cover_loading: bool | None = False
    url: str | None = None

@dataclass
class BandLink:
    social: str | None = None
    url: str | None = None


@dataclass
class BandInformation:
    id: int | None = None
    name: str | None = None
    country: str | None = None
    city: str | None = None
    status: str | None = None
    formed_in: str | None = None
    years_active: str | None = None
    genres: str | None = None
    themes: str | None = None
    label: str | None = None
    current_lineup: list[MemberLineUp] = field(default_factory=list)
    discography: list[AlbumShortInformation] = field(default_factory=list)
    links: list[BandLink] | None = None
    photo_url: str | None = None
    logo_url: str | None = None
    updated_at: datetime | str | None = None
    parsing_error: str | None = None

@dataclass
class BandSearch:
    id: int | None = None
    name: str | None = None
    genre: str | None = None
    country: str | None = None

@dataclass
class AlbumSearch:
    id: int | None = None
    band_id: int | None = None
    band_name: str | None = None
    title: str | None = None
    type: str | None = None
    release_date: str | None = None

