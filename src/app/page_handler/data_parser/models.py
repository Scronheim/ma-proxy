from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel

@dataclass
class SocialLink:
    social: str | None = None
    url: str | None = None

@dataclass
class MemberAlbum:
    id: int | None = None
    title: str | None = None
    title_slug: str | None = None
    release_date: str | None = None
    role: str | None = None

@dataclass
class MemberBand:
    id: int | None = None
    name: str | None = None
    name_slug: str | None = None
    albums: list[MemberAlbum] | None = None
    role: str | None = None

@dataclass
class ShortBandInfo:
    id: int | None = None
    band_name: str | None = None
    band_name_slug: str | None = None

@dataclass
class ShortMember:
    id: int | None = None
    fullname: str | None = None
    fullname_slug: str | None = None
    country: str | None = None
    bands: list[ShortBandInfo] | None = None
    date_of_death: str | None = None
    cause_of_death: str | None = None

@dataclass
class Member:
    id: int | None = None
    fullname: str | None = None
    fullname_slug: str | None = None
    age: str | None = None
    place_of_birth: str | None = None
    gender: str | None = None
    photo_url: str | None = None
    biography: str | None = None
    active_bands: list[MemberBand] | None = field(default_factory=list)
    past_bands: list[MemberBand] | None = field(default_factory=list)
    guest_session: list[MemberBand] | None = field(default_factory=list)
    live: list[MemberBand] | None = field(default_factory=list)
    misc_staff: list[MemberBand] | None = field(default_factory=list)
    links: list[SocialLink] | None = None
    updated_at: datetime | str | None = None

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
class OtherBand:
    id: int | None = None
    name: str | None = None
    name_slug: str | None = None

@dataclass
class MemberLineUp:
    id: int | None = None
    fullname: str | None = None
    fullname_slug: str | None = None
    role: str | None = None
    url: str | None = None
    other_bands: list[OtherBand] = field(default_factory=list)

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
    url: str | None = None

@dataclass
class AlbumInformation:
    id: int | None = None
    title: str | None = None
    title_slug: str | None = None
    band_names: list[str] | None = field(default_factory=list)
    band_names_slug: list[str] | None = field(default_factory=list)
    band_ids: list[int] | None = field(default_factory=list)
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
    title_slug: str | None = None
    type: str | None = None
    release_date: str | None = None
    cover_url: str | None = None
    cover_loading: bool | None = False
    url: str | None = None


@dataclass
class BandInformation:
    id: int | None = None
    name: str | None = None
    name_slug: str | None = None
    description: str | None = None
    country: str | None = None
    city: str | None = None
    status: str | None = None
    formed_in: str | None = None
    years_active: str | None = None
    genres: str | None = None
    themes: str | None = None
    label: str | None = None
    current_lineup: list[MemberLineUp] = field(default_factory=list)
    past_lineup: list[MemberLineUp] = field(default_factory=list)
    discography: list[AlbumShortInformation] = field(default_factory=list)
    links: list[SocialLink] | None = None
    photo_url: str | None = None
    logo_url: str | None = None
    updated_at: datetime | str | None = None
    parsing_error: str | None = None


@dataclass
class BandSearch:
    id: int | None = None
    name: str | None = None
    name_slug: str | None = None
    genres: str | None = None
    country: str | None = None

@dataclass
class BandSearchByLetter(BandSearch):
    status: str | None = None

@dataclass
class SearchByLetterResults:
    total: int
    results: list[BandSearchByLetter]

@dataclass
class RipArtistsResults:
    total: int
    results: list[ShortMember]


@dataclass
class AlbumSearch:
    id: int | None = None
    title: str | None = None
    title_slug: str | None = None
    band_id: int | None = None
    band_name: str | None = None
    band_name_slug: str | None = None
    type: str | None = None
    release_date: str | None = None

