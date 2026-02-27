"""FastAPI ana uygulama."""

import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers.flights import router as flights_router
from backend.middleware.rate_limiter import RateLimiterMiddleware
from backend.middleware.api_key import APIKeyMiddleware

app = FastAPI(
    title="Hafta Sonu Ucus Bulucu API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Rate limiter
rate_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
rate_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))
app.add_middleware(RateLimiterMiddleware, per_minute=rate_per_minute, per_hour=rate_per_hour)

# API key
app.add_middleware(APIKeyMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(flights_router)
