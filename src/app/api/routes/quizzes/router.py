from fastapi import APIRouter
from pymongo import AsyncMongoClient

from app.page_handler.handler import MetalArchivesPageHandler
from .models import QuizzesResponse, QuizResponse


class QuizzesRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/quizzes', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/',
            endpoint=self.get_quizzes,
            response_model=QuizzesResponse,
            tags=['Quizzes'],
            methods=["GET", ]
        )
        self.add_api_route(
            path='/{quiz_id}',
            endpoint=self.get_quiz_by_id,
            response_model=QuizResponse,
            tags=['Quizzes'],
            methods=["GET", ]
        )
        self.db = db

    async def get_quizzes(self) -> QuizzesResponse:
        quizzes = self.db.quizzes.find({})
        quizzes = await quizzes.to_list()
        return QuizzesResponse(
            success=True,
            data=quizzes,
            error=None,
            url='/api/quizzes',
            processing_time=0,
        )
    
    async def get_quiz_by_id(self, quiz_id: int) -> QuizResponse:
        quiz = await self.db.quizzes.find_one({'id': quiz_id})
        return QuizResponse(
            success=True,
            data=quiz,
            error=None,
            url=f"/api/quizzes/{quiz_id}",
            processing_time=0,
        )
