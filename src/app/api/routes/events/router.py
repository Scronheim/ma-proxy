from fastapi import APIRouter, BackgroundTasks
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from app.sse.manager import sse_manager
from .models import LyricsInfoResponse


class EventsRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/events', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/',
            endpoint=self.add_connection,
            response_model=LyricsInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db

    async def add_connection(self):
        return await sse_manager.add_connection()
        

    
