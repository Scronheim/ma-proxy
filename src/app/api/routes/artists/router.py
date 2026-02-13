import dataclasses
from fastapi import APIRouter, BackgroundTasks
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from app.page_handler.data_parser.models import Member, MemberBand, SocialLink
from .models import MemberInfoResponse


class ArtistsRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/artist', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/{member_id}',
            endpoint=self.parse_member,
            response_model=MemberInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db

    async def parse_member(self, background_tasks: BackgroundTasks, member_id: str) -> MemberInfoResponse:
        member = await self._check_member_in_db(int(member_id))
        url = f'https://www.metal-archives.com/artists/please_dont_ban_me/{member_id}'
        
        if member:
            return MemberInfoResponse(
                success=True,
                data=member,
                url=url,
                processing_time=0.0,
            )
        info = self.page_handler.get_member(url=url)
        await self._add_member_in_db(info.data)
        return MemberInfoResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    async def _check_member_in_db(self, member_id: int) -> Member | None:
        result = await self.db.members.aggregate(
            [
                {
                    "$match": {
                        "id": member_id,
                    }
                },
                {"$limit": 1},
            ]
        )
        result = await result.to_list()
        if not result:
            return None
        member = result[0]
        return Member(
            id=member['id'],
            fullname=member['fullname'],
            fullname_slug=member['fullname_slug'],
            age=member['age'],
            place_of_birth=member['place_of_birth'],
            gender=member['gender'],
            biography=member['biography'],
            active_bands=[
                MemberBand(**band)
                for band in member['active_bands']
            ],
            past_bands=[
                MemberBand(**band)
                for band in member['past_bands']
            ],
            guest_session=[
                MemberBand(**band)
                for band in member['guest_session']
            ],
            live=[
                MemberBand(**band)
                for band in member['live']
            ],
            misc_staff=[
                MemberBand(**band)
                for band in member['misc_staff']
            ],
            links=[
                SocialLink(**link)
                for link in member['links']
            ],
            photo_url=member['photo_url'],
            updated_at=member['updated_at']   
        )
    
    async def _add_member_in_db(self, member: Member):
        member_dict = dataclasses.asdict(member)
        await self.db.members.insert_one(member_dict)

