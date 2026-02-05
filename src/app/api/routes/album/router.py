from fastapi import APIRouter
import time

from app.page_handler.handler import MetalArchivesPageHandler
from .models import AlbumInfoResponse


class AlbumRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db, *args, **kwargs):
        super().__init__(prefix='/album', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/{album_id}',
            endpoint=self.get_album_by_id,
            response_model=AlbumInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db

    async def parse_album(self, album_id: int) -> AlbumInfoResponse:
        info = self.page_handler.get_album_info(url='https://www.metal-archives.com/albums/view/id/{album_id}'.format(album_id=album_id))
        return AlbumInfoResponse(
            success=True if info.error is None else False,
            album_info=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def get_album_by_id(self, album_id: str) -> AlbumInfoResponse:
        start_time = time.time()
        album = await self.db.albums.find_one({'id': int(album_id)})
        return AlbumInfoResponse(
            success=True,
            album_info=album,
            error=None,
            url=f'/api/album/{album_id}',
            processing_time=round(time.time() - start_time, 2),
        )

