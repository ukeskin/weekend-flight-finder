"""API key dogrulama middleware."""

import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.database import get_connection


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._public_key = os.getenv("API_KEY_PUBLIC", "")

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        # Health endpoint korumasiz
        if request.url.path == "/api/health":
            return await call_next(request)

        api_key = request.headers.get("x-api-key", "")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required. Provide X-API-Key header."},
            )

        # Oncelikle env variable ile kontrol (hizli yol)
        if api_key == self._public_key and self._public_key:
            return await call_next(request)

        # Veritabanindan kontrol
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, is_active FROM api_keys WHERE key = ?",
                (api_key,),
            ).fetchone()

        if not row or not row["is_active"]:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or inactive API key."},
            )

        return await call_next(request)
