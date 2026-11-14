import asyncio
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.connection import engine
from app.routes.auth import router as auth_router
from app.routes.movies import router as movies_router
from app.routes.recommend import router as recommend_router
from app.routes.watch_history import router as watch_history_router
from app.routes.search_history import router as search_history_router
from app.routes.ratings import router as ratings_router
from app.routes.watchlist import router as watchlist_router
from app.routes.admin import router as admin_router
from app.services.tmdb.movies import (
    get_trending_movies, get_top_rated_movies, get_upcoming_movies,
)
from app.services.tmdb.client import aclose_client
from app.schedular.schedular import start_scheduler, stop_scheduler

configure_logging()
logger = logging.getLogger("deepcine")

app = FastAPI(
    title="DeepCine AI API",
    version="1.1.0",
    description="AI-Powered Personalized Movie Recommendation System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(recommend_router)
app.include_router(watch_history_router)
app.include_router(search_history_router)
app.include_router(ratings_router)
app.include_router(watchlist_router)
app.include_router(admin_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
            request_id, request.method, request.url.path, duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.on_event("startup")
async def warm_up_caches():
    async def _warm():
        try:
            await asyncio.gather(
                get_trending_movies(),
                get_top_rated_movies(),
                get_upcoming_movies(),
            )
            logger.info("TMDB cache warm-up complete.")
        except Exception:
            logger.exception("TMDB cache warm-up failed.")

    asyncio.create_task(_warm())
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
    await aclose_client()


@app.get("/")
def root():
    return {"message": "Welcome to DeepCine AI - Personalized Movie Recommendations 🚀"}


@app.get("/health")
def health():
    """Backward-compatible liveness endpoint."""
    return health_live()


@app.get("/health/live")
def health_live():
    """Liveness: confirms the API process can serve requests."""
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready():
    """Readiness: confirms the API can reach its primary database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Readiness check failed: database unavailable.")
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        )
    return {"status": "ready", "database": "ok"}
