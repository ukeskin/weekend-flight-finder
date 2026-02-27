"""IP bazli sliding window rate limiting middleware."""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int = 60, per_hour: int = 500):
        super().__init__(app)
        self.per_minute = per_minute
        self.per_hour = per_hour
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, now: float):
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        cutoff = now - 3600
        keys_to_delete = []
        for ip, timestamps in self._requests.items():
            self._requests[ip] = [t for t in timestamps if t > cutoff]
            if not self._requests[ip]:
                keys_to_delete.append(ip)
        for k in keys_to_delete:
            del self._requests[k]

    def _check_rate(self, ip: str, now: float) -> tuple[bool, int, int]:
        with self._lock:
            self._cleanup(now)
            timestamps = self._requests[ip]

            minute_ago = now - 60
            hour_ago = now - 3600
            minute_count = sum(1 for t in timestamps if t > minute_ago)
            hour_count = sum(1 for t in timestamps if t > hour_ago)

            if minute_count >= self.per_minute:
                remaining = 0
                reset = int(min(t for t in timestamps if t > minute_ago) + 60 - now) + 1
                return False, remaining, reset

            if hour_count >= self.per_hour:
                remaining = 0
                reset = int(min(t for t in timestamps if t > hour_ago) + 3600 - now) + 1
                return False, remaining, reset

            timestamps.append(now)
            remaining = min(self.per_minute - minute_count - 1, self.per_hour - hour_count - 1)
            return True, remaining, 0

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()
        allowed, remaining, reset = self._check_rate(ip, now)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
