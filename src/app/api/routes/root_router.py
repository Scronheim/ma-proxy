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
from .song import SongRouter
from .file_manager import create_file_manager_router


class RootRouter(APIRouter):

    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/api' ,*args, **kwargs)

        band_router = BandRouter(page_handler=page_handler, db=db)
        album_router = AlbumRouter(page_handler=page_handler, db=db)
        lyrics_router = LyricsRouter(page_handler=page_handler, db=db)
        stats_router = StatsRouter(page_handler=page_handler, db=db)
        artists_router = ArtistsRouter(page_handler=page_handler, db=db)
        song_router = SongRouter(page_handler=page_handler, db=db)

        events_router = EventsRouter(page_handler=page_handler, db=db)

        auth_router = AuthRouter(page_handler=page_handler, db=db)
        
        self.include_router(router=band_router)
        self.include_router(router=album_router)
        self.include_router(router=lyrics_router)
        self.include_router(router=stats_router)
        self.include_router(router=artists_router)
        self.include_router(router=song_router)

        self.include_router(router=events_router)

        self.include_router(router=auth_router)

        file_manager_router = create_file_manager_router(
            base_directory="/mnt/data/music",
            route_prefix="/files",
            allow_delete=True,
            allow_rename=True,
            allow_move=True,
            allow_copy=True,
            allow_upload=True,
            allow_create_folder=True,
            max_file_size=10 * 1024 * 1024 * 1024,  # 10 GB
            allowed_extensions=[".jpg", ".jpeg", ".png", ".mp3", ".flac", ".zip", ".7z", ".rar"]
        )

        self.include_router(router=file_manager_router)
