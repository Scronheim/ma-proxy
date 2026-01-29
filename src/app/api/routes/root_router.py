from fastapi.routing import APIRouter

from app.page_handler.handler import MetalArchivesPageHandler
from .band import BandRouter
from .album import AlbumRouter


class RootRouter(APIRouter):

    def __init__(self, page_handler: MetalArchivesPageHandler,*args, **kwargs):
        super().__init__(prefix='/api' ,*args, **kwargs)

        band_router = BandRouter(page_handler=page_handler)
        album_router = AlbumRouter(page_handler=page_handler)
        self.include_router(router=band_router)
        self.include_router(router=album_router)
