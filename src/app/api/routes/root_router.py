from fastapi.routing import APIRouter
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from .band import BandRouter
from .album import AlbumRouter


class RootRouter(APIRouter):

    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/api' ,*args, **kwargs)

        band_router = BandRouter(page_handler=page_handler, db=db)
        album_router = AlbumRouter(page_handler=page_handler, db=db)
        
        self.include_router(router=band_router)
        self.include_router(router=album_router)
