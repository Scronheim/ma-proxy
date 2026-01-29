from fastapi import APIRouter, HTTPException, Query
from urllib.parse import quote
import httpx
import re

from app.page_handler.handler import MetalArchivesPageHandler
from .models import BandInfoResponse, BandSearchResponse


class BandRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, *args, **kwargs):
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

    async def parse_random(self) -> BandInfoResponse:
        info = self.page_handler.get_band_info(url='https://www.metal-archives.com/band/random')
        
        return BandInfoResponse(
            success=True if info.error is None else False,
            band_info=info.data,
            error=info.error,
            url=info.url,
            processing_time=info.processing_time,
        )
    
    async def parse_band_by_id(self, band_id: str) -> BandInfoResponse:
        info = self.page_handler.get_band_info(url='https://www.metal-archives.com/band/view/id/{band_id}'.format(band_id=band_id))
        
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

