from fastapi import FastAPI

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
        router = RootRouter(page_handler=self.page_handler)
        self.include_router(router=router)
