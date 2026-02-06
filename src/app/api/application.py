from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient

from app.api.routes.root_router import RootRouter
from app.page_handler.handler import MetalArchivesPageHandler


class MetalParserAPI(FastAPI):
    def __init__(self, page_handler: MetalArchivesPageHandler, *args, **kwargs):
        super().__init__(
            title="Metal Archives Parser API",
            description="API для парсинга страниц Metal Archives",
            version='1.0.0',
            *args, **kwargs,
        )
        self.page_handler = page_handler
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        client = AsyncMongoClient('mongodb://scronheim:010503Qq@localhost:27017/')
        db = client.ma

        router = RootRouter(page_handler=self.page_handler, db=db)
        self.include_router(router=router)
