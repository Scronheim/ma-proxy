from fastapi import APIRouter
from pymongo import AsyncMongoClient

from app.page_handler.data_parser.models import StatInfo, AllStatInfo, BandStatInfo
from app.page_handler.handler import MetalArchivesPageHandler
from .models import StatsInfoResponse


class StatsRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/stats', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/',
            endpoint=self.get_stats,
            response_model=StatsInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db

    async def get_stats(self) -> StatsInfoResponse:
        info = self.page_handler.get_stats(url='https://www.metal-archives.com/stats')
        local = await self.get_local_stats()
        stats = AllStatInfo(local=local, ma=info.data)
        return StatsInfoResponse(
            success=True if info.error is None else False,
            data=stats,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def get_local_stats(self) -> StatInfo:
        stats = await self.db.bands.aggregate([
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ])
        stats_list = await stats.to_list()
        active = list(filter(lambda x: x["_id"] == 'Active', stats_list))[0]['count']
        on_hold = list(filter(lambda x: x["_id"] == 'On hold', stats_list))[0]['count']
        split_up = list(filter(lambda x: x["_id"] == 'Split-up', stats_list))[0]['count']
        changed_name = list(filter(lambda x: x["_id"] == 'Changed name', stats_list))[0]['count']
        unknown = list(filter(lambda x: x["_id"] == 'Unknown', stats_list))[0]['count']
        total = active + on_hold + split_up + changed_name + unknown
        bands = BandStatInfo(
            active=active, on_hold=on_hold, split_up=split_up,
            changed_name=changed_name, unknown=unknown, total=total)

        albums = await self.db.albums.count_documents({})
        songs_result = await self.db.albums.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_tracks': {
                        '$sum': {'$size': '$tracklist'}
                    }
                }
            }
        ])
        songs_list = await songs_result.to_list()
        songs = songs_list[0]['total_tracks']
        return StatInfo(bands=bands, albums=int(albums), songs=int(songs))
   