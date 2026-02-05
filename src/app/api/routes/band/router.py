from fastapi import APIRouter, Query
from urllib.parse import quote

from datetime import datetime
from typing import Union, Optional, Dict, Tuple
from bson.json_util import dumps
import dataclasses
import json
import asyncio

from app.page_handler.handler import MetalArchivesPageHandler
from app.api.routes.album import AlbumRouter
from app.page_handler.data_parser.models import BandInformation, AlbumInformation
from .models import BandInfoResponse, BandSearchResponse


class BandRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db, *args, **kwargs):
        super().__init__(prefix='/band', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/random',
            endpoint=self.parse_random,
            response_model=BandInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.add_api_route(
            path='/search',
            endpoint=self.search_bands,
            response_model=BandSearchResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.add_api_route(
            path='/{band_id}',
            endpoint=self.parse_band_by_id,
            response_model=BandInfoResponse,
            tags=['Parsing'],
            methods=["GET", ]
        )
        self.db = db
        

    async def parse_random(self) -> BandInfoResponse:
        info = self.page_handler.get_band_info(url='https://www.metal-archives.com/band/random')
        asyncio.create_task(self._replace_band_in_db(info.data))
        return BandInfoResponse(
            success=True if info.error is None else False,
            band_info=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def parse_band_by_id(self, band_id: str) -> BandInfoResponse:
        band = await self._check_band_in_db(int(band_id))
        info = {}
        url = 'https://www.metal-archives.com/band/view/id/{band_id}'.format(band_id=band_id)
        if band:
            diff = self._get_date_difference(band['updated_at']['$date'])
            if diff['days'] > 15:
                band = self.page_handler.get_band_info(url=url).data
                asyncio.create_task(self._replace_band_in_db(band))
            return BandInfoResponse(
                success=True,
                band_info=BandInformation(
                    id=band['id'],
                    name=band['name'],
                    country=band['country'],
                    city=band['city'],
                    status=band['status'],
                    formed_in=band['formed_in'],
                    years_active=band['years_active'],
                    genres=band['genres'],
                    themes=band['themes'],
                    current_lineup=band['current_lineup'],
                    discography=band['discography'],
                    label=band['label'],
                    photo_url=band['photo_url'],
                    logo_url=band['logo_url'],
                    parsing_error=band['parsing_error']
            ),
                error='',
                url='',
                processing_time=0.0,
            )    
        else:
            info = self.page_handler.get_band_info(url=url)
            await self._replace_band_in_db(info.data)
        return BandInfoResponse(
            success=True if info.error is None else False,
            band_info=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def search_bands(self, query: str = Query(..., description="Search query")):
        """
        Search for bands on Metal Archives
        """
        encoded_query = quote(query.strip())
        search_url = f"https://www.metal-archives.com/search/ajax-band-search/?field=name&query={encoded_query}"
        info = self.page_handler.search_band_info(search_url)
        
        return BandSearchResponse(
            success=True if info.error is None else False,
            bands=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    async def _check_album_in_db(self, album_id: int) -> AlbumInformation | None:
        result = await self.db.albums.find_one({'id': album_id})
        return result
    
    async def _check_band_in_db(self, band_id: int) -> BandInformation | None:
        result = await self.db.bands.aggregate([
            {
                "$match": {
                    "id": band_id,
                }
            },
            { "$limit": 1 },
            {
                "$lookup": {
                    "from": "albums",
                    "localField": "discography",
                    "foreignField": "_id",
                    "as": "discography"
                }
            }
        ])
        result = await result.to_list()
        if len(result) > 0:
            return json.loads(dumps(result[0]))
        return None
    
    async def _replace_band_in_db(self, band: BandInformation):
        band_dict = dataclasses.asdict(band)
        band_dict['updated_at'] = datetime.now()
        album_ids = []
        for album in band_dict['discography']:
            router = AlbumRouter(page_handler=self.page_handler, db=self.db)
            album_response = await router.parse_album(album_id=album['id'])
            album_dict = dataclasses.asdict(album_response.album_info)
            album_dict['updated_at'] = datetime.now()
            new_album = await self.db.albums.replace_one({'id': album['id']}, album_dict, upsert=True)
            album_ids.append(new_album.upserted_id)

        band_dict['discography'] = album_ids
        await self.db.bands.replace_one({'id': band.id}, band_dict, upsert=True)
    
    def _get_date_difference(self, target_date: Union[str, datetime], date_format: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> Dict[str, int]:
        # Получаем текущую дату и время 2026-02-04T23:25:54.239Z
        current_datetime = datetime.now()
        
        # Конвертируем target_date в datetime если это строка
        if isinstance(target_date, str):
            try:
                target_datetime = datetime.strptime(target_date, date_format)
            except ValueError:
                raise ValueError(f"Неверный формат даты. Ожидается: {date_format}")
        else:
            target_datetime = target_date
        
        # Вычисляем разницу
        time_difference = current_datetime - target_datetime
        
        # Извлекаем компоненты разницы
        days = time_difference.days
        seconds = time_difference.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'total_seconds': int(time_difference.total_seconds()),
            'total_days': days + seconds / 86400,
            'is_future': time_difference.total_seconds() < 0
        }
