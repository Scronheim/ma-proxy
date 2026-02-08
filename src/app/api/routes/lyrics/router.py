from fastapi import APIRouter, BackgroundTasks
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from .models import LyricsInfoResponse


class LyricsRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/lyrics', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/',
            endpoint=self.parse_lyrics,
            response_model=LyricsInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db

    async def parse_lyrics(self, background_tasks: BackgroundTasks, id: str, album_id: str = '',) -> LyricsInfoResponse:
        info = self.page_handler.get_lyrics(
            url=f'https://www.metal-archives.com/release/ajax-view-lyrics/id/{id}'
        )
        background_tasks.add_task(self.update_lyrics, lyrics_id=id, album_id=album_id, text=info.data)
        return LyricsInfoResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    async def update_lyrics(self, lyrics_id: str, album_id: str = '', text: str = '') -> LyricsInfoResponse:
        await self.db.albums.update_one({
                    "id": int(album_id),
                    "tracklist.id": int(lyrics_id)
                },
                {
                    "$set": {
                        "tracklist.$.lyrics": text
                    }
                }
            )
