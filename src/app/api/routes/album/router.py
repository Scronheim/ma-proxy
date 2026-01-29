from fastapi import APIRouter

from app.page_handler.handler import MetalArchivesPageHandler
from .models import AlbumInfoResponse


class AlbumRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(prefix='/album', *args, **kwargs)
        self.add_api_route(
            path='/{album_id}',
            endpoint=self.parse_album,
            response_model=AlbumInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )

    @staticmethod
    async def parse_album(album_id: str) -> AlbumInfoResponse:
        handler = MetalArchivesPageHandler()
        info = handler.get_album_info(url='https://www.metal-archives.com/albums/view/id/{album_id}'.format(album_id=album_id))
        return AlbumInfoResponse(
            success=True if info.error is None else False,
            album_info=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

