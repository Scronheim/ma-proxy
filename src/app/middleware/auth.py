from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.security import decode_access_token

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, users_collection, exclude_paths: list = None):
        super().__init__(app)
        self.users_collection = users_collection
        self.exclude_paths = exclude_paths or [
            "/register", "/login", "/docs", "/redoc", "/openapi.json", "/"
        ]

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"},
            )

        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
            )

        email = payload.get("sub")
        if not email:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
            )

        user = await self.users_collection.find_one({"email": email})
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "User not found"},
            )

        request.state.user = user
        return await call_next(request)
