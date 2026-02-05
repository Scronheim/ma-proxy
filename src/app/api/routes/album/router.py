from fastapi import APIRouter
from urllib.parse import quote
import time

from app.page_handler.handler import MetalArchivesPageHandler
from .models import AlbumInfoResponse, SearchResponse


class AlbumRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db, *args, **kwargs):
        super().__init__(prefix='/album', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/search',
            endpoint=self.search_albums,
            response_model=SearchResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
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
        if not album:
            return await self.parse_album(int(album_id))
        return AlbumInfoResponse(
            success=True,
            album_info=album,
            error=None,
            url=f'/api/album/{album_id}',
            processing_time=round(time.time() - start_time, 2),
        )

    async def search_albums(self, query: str) -> SearchResponse:
        """
        Search for albums on Metal Archives
        """
        encoded_query = quote(query.strip())
        search_url = f"https://www.metal-archives.com/search/ajax-album-search/?field=title&query={encoded_query}"
        info = self.page_handler.search_album_info(search_url)
        return SearchResponse(
            success=True if info.error is None else False,
            results=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
