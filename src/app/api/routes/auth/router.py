import re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Request, status
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

from app.page_handler.handler import MetalArchivesPageHandler
from app.models.user import UserCreate, UserLogin, UserInDB, Me, Token
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.config import settings

class AuthRouter(APIRouter):
    def __init__(self, page_handler: MetalArchivesPageHandler, db: AsyncMongoClient, *args, **kwargs):
        super().__init__(prefix='/auth', *args, **kwargs)
        self.page_handler = page_handler
        self.add_api_route(
            path='/register',
            endpoint=self.register,
            response_model=Token,
            tags=['Auth'],
            methods=['POST']
        )
        self.add_api_route(
            path='/login',
            endpoint=self.login,
            response_model=Token,
            tags=['Auth'],
            methods=['POST']
        )
        self.add_api_route(
            path='/me',
            endpoint=self.me,
            response_model=Me,
            tags=['Auth'],
            methods=['GET']
        )
        self.add_api_route(
            path='/me/update',
            endpoint=self.update_me,
            response_model=Me,
            tags=['Auth'],
            methods=['PATCH']
        )
        self.add_api_route(
            path='/profile/{username}',
            endpoint=self.get_user_profile,
            response_model=Me,
            tags=['Auth'],
            methods=['GET']
        )
        self.db = db

    async def register(self, user_data: UserCreate):
        existing = await self._get_user_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(user_data.password)
        user_doc = {
            "username": user_data.username,
            "password": hashed_password,
            "real_name": None,
            "gender": None,
            "country": None,
            "favorite_bands": [],
            "favorite_albums": [],
            "role": "user",
            "created_at": datetime.now(timezone.utc),
        }

        try:
            await self.db.users.insert_one(user_doc)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        access_token = create_access_token(
            data={"sub": user_data.username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"token": access_token, "user": Me(**user_doc)}
    
    async def login(self, form_data: UserLogin):
        user = await self._get_user_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user[0]["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        access_token = create_access_token(
            data={"sub": user[0]["username"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"token": access_token, "user": Me(**user[0])}
    
    async def me(self, request: Request):
        payload = decode_access_token(request.headers['authorization'])
        user = await self._get_user_by_username(payload['sub'])
        if user:
            return Me(**user[0])
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
    
    async def update_me(self, request: Request, form_data: UserInDB):
        payload = decode_access_token(request.headers['authorization'])
        await self.db.users.update_one({'username': payload['sub']}, {'$set': form_data.model_dump()})
        user = await self._get_user_by_username(payload['sub'])
        return Me(**user[0])

    async def get_user_profile(self, username: str):
        user = await self._get_user_by_username(username)
        if user:
            return Me(**user[0])
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    async def _get_user_by_username(self, username: str):
        pipeline = [
            {
                "$match": {
                    "username": re.compile(f"^{username}$", re.IGNORECASE),
                }
            },
            {"$limit": 1},
            {
                '$lookup': {
                    'from': 'bands',
                    'localField': 'favorite_bands',
                    'foreignField': 'id',
                    'as': 'favorite_bands',
                }
            },
            {
                '$lookup': {
                    'from': 'albums',
                    'localField': 'favorite_albums',
                    'foreignField': 'id',
                    'as': 'favorite_albums',
                }
            },
            {
                "$project": {
                    "username": 1,
                    "password": 1,
                    "real_name": 1,
                    "gender": 1,
                    "country": 1,
                    "created_at": 1,
                    "favorite_bands.id": 1,
                    "favorite_bands.name": 1,
                    "favorite_bands.name_slug": 1,
                    "favorite_bands.genres": 1,
                    "favorite_bands.country": 1,
                    "favorite_bands.photo_url": 1,
                    "favorite_bands.logo_url": 1,
                    "favorite_albums.id": 1,
                    "favorite_albums.title": 1,
                    "favorite_albums.title_slug": 1,
                    "favorite_albums.band_names": 1,
                    "favorite_albums.band_names_slug": 1,
                    "favorite_albums.release_date": 1,
                    "favorite_albums.type": 1,
                    "favorite_albums.cover_url": 1,
                }
            }
        ]
        result = await self.db.users.aggregate(pipeline)
        return await result.to_list()
