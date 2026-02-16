import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
    MONGO_USER: str = os.getenv("MONGO_USER", "")
    MONGO_PASS: str = os.getenv("MONGO_PASS", "")
    MONGO_DB: str = os.getenv("MONGO_DB", "ma")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 44640

settings = Settings()
