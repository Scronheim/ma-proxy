from pydantic import BaseModel

from app.page_handler.data_parser.models import Quiz

class QuizResponse(BaseModel):
    """Модель ответа с информацией о викторине"""
    success: bool
    data: Quiz | None = []
    error: str | None = None
    url: str
    processing_time: float

class QuizzesResponse(BaseModel):
    """Модель ответа с информацией о викторинах"""
    success: bool
    data: list[Quiz] | None = []
    error: str | None = None
    url: str
    processing_time: float
