import datetime

from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class ShortBandInfo(BaseModel):
    id: int | None = None
    name: str | None = None
    name_slug: str | None = None
    country: str | None = None
    genres: str | None = None
    photo_url: str | None = None
    logo_url: str | None = None

class ShortAlbumInfo(BaseModel):
    id: int | None = None
    title: str | None = None
    title_slug: str | None = None
    band_names: list[str] | None = None
    band_names_slug: list[str] | None = None
    release_date: str | None = None
    type: str | None = None
    cover_url: str | None = None

class Rating(BaseModel):
    id: int
    rating: float

class Me(BaseModel):
    username: str | None = None
    real_name: str | None = None
    gender: str | None = None
    country: str | None = None
    role: str = 'user'
    avatar_color: str = 'red'
    favorite_genre: str | None = None
    bands_ratings: list[Rating] = Field(default_factory=list)
    albums_ratings: list[Rating] = Field(default_factory=list)
    favorite_bands: list[ShortBandInfo] | list[int] = Field(default_factory=list)
    favorite_albums: list[ShortAlbumInfo] | list[int] = Field(default_factory=list)
    created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

class Token(BaseModel):
    user: Me | None = None
    token: str | None = None
