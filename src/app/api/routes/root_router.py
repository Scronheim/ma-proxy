from fastapi.routing import APIRouter

from .band import BandRouter
from .album import AlbumRouter


class RootRouter(APIRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(prefix='/api' ,*args, **kwargs)

        band_router = BandRouter()
        album_router = AlbumRouter()
        self.include_router(router=band_router)
        self.include_router(router=album_router)
