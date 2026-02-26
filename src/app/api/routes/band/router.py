import dataclasses
from datetime import datetime
from typing import Dict, Union
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pymongo import AsyncMongoClient

from app.page_handler.data_parser.models import AlbumInformation, AlbumShortInformation, BandInformation, MemberLineUp, OtherBand
from app.page_handler.handler import MetalArchivesPageHandler
from app.sse.manager import sse_manager

from .models import BandInfoResponse, SearchResponse, SocialLink, SearchByLetterResponse

from app.messages import get_start_random_message, get_new_album_message,\
                         get_album_number_message
from app.utils.utils import slug_string


class BandRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/band', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/random',
            endpoint=self.parse_random,
            response_model=BandInfoResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.add_api_route(
            path='/search',
            endpoint=self.search_bands,
            response_model=SearchResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.add_api_route(
            path='/search/letter/{letter}',
            endpoint=self.search_band_by_letter,
            response_model=SearchByLetterResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.add_api_route(
            path='/search/country/{country}',
            endpoint=self.search_band_by_country,
            response_model=SearchByLetterResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.add_api_route(
            path='/{band_id}',
            endpoint=self.parse_band_by_id,
            response_model=BandInfoResponse,
            tags=['Parsing'],
            methods=["GET"]
        )
        self.db = db

    async def search_band_by_country(self, country: str, page: str = '1') -> SearchByLetterResponse:
        offset = (int(page) - 1) * 500
        
        info = self.page_handler.get_bands_by_country(url=f'https://www.metal-archives.com/browse/ajax-country/c/{country}?iDisplayStart={offset}&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1')
        return SearchByLetterResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def search_band_by_letter(self, letter: str, page: str = '1') -> SearchByLetterResponse:
        if len(letter) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Длина должна быть до 3ёх символов"
        )
        offset = (int(page) - 1) * 500
        info = self.page_handler.get_bands_by_letter(url=f'https://www.metal-archives.com/browse/ajax-letter/l/{letter}?iDisplayStart={offset}')
        return SearchByLetterResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    
    async def parse_random(self, background_tasks: BackgroundTasks) -> BandInfoResponse:
        await sse_manager.send_message(get_start_random_message())
        info = self.page_handler.get_band_info(url='https://www.metal-archives.com/band/random')
        band = await self._check_band_in_db(int(info.data.id))
        if not band:
            await self._add_band_in_db(info.data)
        background_tasks.add_task(self._replace_band_in_db, band=info.data)
        return BandInfoResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    async def parse_band_by_id(self, band_id: str, background_tasks: BackgroundTasks) -> BandInfoResponse:
        band = await self._check_band_in_db(int(band_id))
        url = 'https://www.metal-archives.com/band/view/id/{band_id}'.format(band_id=band_id)
        if band:
            diff = self._get_date_difference(target_date=band.updated_at)
            if (band.status == 'Active' or band.status == 'On Hold' or band.status == 'Unknown') and diff['days'] > 15:
                page_info = self.page_handler.get_band_info(url=url)
                background_tasks.add_task(self._replace_band_in_db, band=page_info.data)

            return BandInfoResponse(
                success=True,
                data=band,
                url=url,
                processing_time=0.0,
            )
        
        info = self.page_handler.get_band_info(url=url)
        await self._add_band_in_db(info.data)
        background_tasks.add_task(self._replace_band_in_db, band=info.data)
        return BandInfoResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    async def search_bands(self, query: str) -> SearchResponse:
        """
        Search for bands on Metal Archives
        """
        encoded_query = quote(query.strip())
        search_url = f"https://www.metal-archives.com/search/ajax-band-search/?field=name&query={encoded_query}"
        info = self.page_handler.search_band_info(search_url)

        return SearchResponse(
            success=True if info.error is None else False,
            data=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )

    async def _check_album_in_db(self, album_id: int) -> AlbumInformation | None:
        result = await self.db.albums.find_one({'id': album_id})
        return result

    async def _check_band_in_db(self, band_id: int) -> BandInformation | None:
        result = await self.db.bands.aggregate(
            [
                {
                    "$match": {
                        "id": band_id,
                    }
                },
                {"$limit": 1},
                {
                    "$lookup": {
                        "from": "albums",
                        "localField": "discography",
                        "foreignField": "_id",
                        "as": "discography"
                    }
                }
            ]
        )
        result = await result.to_list()
        if not result:
            return None

        band = result[0]
        return BandInformation(
            id=band['id'],
            name=band['name'],
            name_slug=band['name_slug'],
            description=band['description'],
            country=band['country'],
            city=band['city'],
            status=band['status'],
            formed_in=band['formed_in'],
            years_active=band['years_active'],
            genres=band['genres'],
            themes=band['themes'],
            current_lineup=[
                MemberLineUp(
                    id=member['id'],
                    fullname=member['fullname'],
                    fullname_slug=member['fullname_slug'],
                    role=member['role'],
                    other_bands=[
                        OtherBand(**other_band)
                        for other_band in member['other_bands']
                    ],
                    url=member['url']
                )
                for member in band['current_lineup']
            ],
            past_lineup=[
                MemberLineUp(
                    id=member['id'],
                    fullname=member['fullname'],
                    fullname_slug=member['fullname_slug'],
                    role=member['role'],
                    other_bands=[
                        OtherBand(**other_band)
                        for other_band in member['other_bands']
                    ],
                    url=member['url']
                )
                for member in band['past_lineup']
            ],
            discography=[
                AlbumShortInformation(
                    id=disc['id'],
                    title=disc['title'],
                    title_slug=slug_string(disc['title']),
                    type=disc['type'],
                    cover_url=disc['cover_url'],
                    release_date=disc['release_date'],
                    cover_loading=False,
                    url=disc['url'],
                )
                for disc in band['discography']
            ],
            links=[
                SocialLink(**link)
                for link in band['links']
            ],
            label=band['label'],
            photo_url=band['photo_url'],
            logo_url=band['logo_url'],
            updated_at=band['updated_at'],
            parsing_error=band['parsing_error']
        )
    
    async def _add_band_in_db(self, band: BandInformation):
        band_dict = dataclasses.asdict(band)
        await self.db.bands.insert_one(band_dict)
    
    async def _replace_band_in_db(self, band: BandInformation):
        album_record_ids = []
        for album in band.discography:
            album_exist = await self.db.albums.find_one({'id': album.id})
            if album_exist:
                album_record_ids.append(album_exist.get('_id'))
                album_exist.pop('_id')
                album_model = AlbumInformation(**album_exist)
                await sse_manager.send_message(get_new_album_message(album_model))
                continue

            album_page_info = self.page_handler.get_album_info(
                url=f'https://www.metal-archives.com/albums/view/id/{album.id}'
            )
            new_album = await self.db.albums.insert_one(dataclasses.asdict(album_page_info.data))
            await sse_manager.send_message(get_new_album_message(album_page_info.data))
            album_record_ids.append(new_album.inserted_id)

        band.discography = album_record_ids
        await sse_manager.send_message(get_album_number_message(len(album_record_ids)))
        await self.db.bands.replace_one({'id': band.id}, dataclasses.asdict(band), upsert=True)

    @staticmethod
    def _get_date_difference(
        target_date: Union[str, datetime],
        date_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    ) -> Dict[str, int]:
        current_datetime = datetime.now()
        if isinstance(target_date, str):
            try:
                target_datetime = datetime.strptime(target_date, date_format)
            except ValueError:
                raise ValueError(f"Неверный формат даты. Ожидается: {date_format}")
        else:
            target_datetime = target_date

        time_difference = current_datetime - target_datetime

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
