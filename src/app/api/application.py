import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient

from app.api.routes.root_router import RootRouter
from app.page_handler.handler import MetalArchivesPageHandler
from app.middleware.auth import AuthMiddleware

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MONGO_PORT', 27017)
MONGO_USER = os.environ.get('MONGO_USER', '')
MONGO_PASS = os.environ.get('MONGO_PASS', '')
MONGO_DB = os.environ.get('MONGO_DB', 'ma')


class MetalParserAPI(FastAPI):
    def __init__(self, page_handler: MetalArchivesPageHandler, *args, **kwargs):
        super().__init__(
            title="Metal Archives Parser API",
            description="API для парсинга страниц Metal-Archives.com",
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

        client = AsyncMongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/')
        db = client[MONGO_DB]
        self.add_middleware(
            AuthMiddleware,
            users_collection=db['users'],
            exclude_paths=['/register', '/login', '/docs', '/redoc', '/openapi.json', '/']
        )

        router = RootRouter(page_handler=self.page_handler, db=db)
        self.include_router(router=router)
