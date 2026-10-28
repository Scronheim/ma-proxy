import dataclasses
from fastapi import APIRouter, BackgroundTasks
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from app.page_handler.data_parser.models import Member, MemberBand, SocialLink
from .models import UpcomingReleasesInfoResponse


class ReleaseRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/release', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/upcoming',
            endpoint=self.parse_upcoming_releases,
            response_model=UpcomingReleasesInfoResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.db = db

    async def parse_upcoming_releases(self, page: str = '1') -> UpcomingReleasesInfoResponse:
        offset = (int(page) - 1) * 100
        info = self.page_handler.get_upcoming_releases(
            url=f'https://www.metal-archives.com/release/ajax-upcoming/json?iDisplayStart={offset}&iDisplayLength=100'
        )
        return UpcomingReleasesInfoResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

