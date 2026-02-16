from fastapi.routing import APIRouter
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from .band import BandRouter
from .album import AlbumRouter
from .lyrics import LyricsRouter
from .events import EventsRouter
from .stats import StatsRouter
from .artists import ArtistsRouter
from .auth import AuthRouter


class RootRouter(APIRouter):

    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/api' ,*args, **kwargs)

        band_router = BandRouter(page_handler=page_handler, db=db)
        album_router = AlbumRouter(page_handler=page_handler, db=db)
        lyrics_router = LyricsRouter(page_handler=page_handler, db=db)
        stats_router = StatsRouter(page_handler=page_handler, db=db)
        artists_router = ArtistsRouter(page_handler=page_handler, db=db)

        events_router = EventsRouter(page_handler=page_handler, db=db)

        auth_router = AuthRouter(page_handler=page_handler, db=db)
        
        self.include_router(router=band_router)
        self.include_router(router=album_router)
        self.include_router(router=lyrics_router)
        self.include_router(router=stats_router)
        self.include_router(router=artists_router)

        self.include_router(router=events_router)

        self.include_router(router=auth_router)
