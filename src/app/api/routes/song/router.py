from fastapi import APIRouter, Request
from pymongo import AsyncMongoClient
from urllib.parse import urlencode

from app.api.routes.band.models import SearchByResponse
from app.page_handler.handler import MetalArchivesPageHandler
from .models import SongInfoResponse


class SongRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/song', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/search/advanced',
            endpoint=self.advance_search,
            response_model=SearchByResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.db = db

    async def advance_search(self, request: Request) -> SearchByResponse:
        query = dict(request.query_params)
        page = query.get('page', 1)
        offset = (int(page) - 1) * 500
        query['iDisplayStart'] = offset
        info = self.page_handler.advanced_song_search(url=f'https://www.metal-archives.com/search/ajax-advanced/searching/songs/?{urlencode(query)}')
        return SearchByResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
