from fastapi import FastAPI

from app.api.routes.root_router import RootRouter


class MetalParserAPI(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(
            title="Metal Archives Parser API",
            description="API для парсинга страниц Metal Archives",
            version='1.0.0',
            *args, **kwargs,
        )
        router = RootRouter()
        self.include_router(router=router)
