import asyncio
import logging
import time

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine
from app.core.config import settings
from app.models import (
    User, Movie, Genre, MovieGenre, WatchHistory, SearchHistory,
    Rating, WatchlistItem,
)
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
from ai.artifact_storage import download_artifacts_from_gcs
from ai.recommender import _get_index_and_ids
from app.schedular.schedular import start_scheduler, stop_scheduler

logger = logging.getLogger("deepcine")
content_artifacts_ready = False


def initialize_database() -> None:
    """Create missing tables after the API process starts.

    Neon may need a few seconds to resume a suspended compute. Retry transient
    connection failures rather than failing during Python module import.
    """
    for attempt in range(1, 6):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema check complete.")
            return
        except OperationalError:
            if attempt == 5:
                logger.exception("Could not connect to the database during startup.")
                raise

            delay = min(2 ** (attempt - 1), 8)
            logger.warning(
                "Database connection attempt %s/5 failed; retrying in %s seconds.",
                attempt,
                delay,
            )
            time.sleep(delay)


app = FastAPI(
    title="DeepCine AI API",
    version="1.0.0",
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


@app.on_event("startup")
async def warm_up_caches():
    # Database work happens after module import, and the worker thread keeps
    # synchronous SQLAlchemy operations off the event loop.
    await asyncio.to_thread(initialize_database)

    global content_artifacts_ready
    if settings.GCS_BUCKET.strip():
        # Download, checksum-validate, and load one complete artifact generation
        # before the instance begins serving recommendation traffic.
        await asyncio.to_thread(download_artifacts_from_gcs)
        await asyncio.to_thread(_get_index_and_ids)
        content_artifacts_ready = True
        logger.info("Content recommender artifacts are ready.")
    else:
        logger.warning(
            "GCS_BUCKET is unset; content-based recommendations may be unavailable."
        )

    async def _warm():
        try:
            await asyncio.gather(
                get_trending_movies(),
                get_top_rated_movies(),
                get_upcoming_movies(),
            )
            logger.info("TMDB cache warm-up complete.")
        except Exception as exc:  # pragma: no cover
            logger.warning("TMDB cache warm-up failed: %s", exc)

    asyncio.create_task(_warm())

    if settings.ENABLE_SCHEDULER:
        start_scheduler()
    else:
        logger.info("In-process scheduler disabled by ENABLE_SCHEDULER=false.")


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
    await aclose_client()


@app.get("/")
def root():
    return {"message": "Welcome to DeepCine AI - Personalized Movie Recommendations 🚀"}


@app.get("/health")
def health():
    """Readiness check: verify the API process can reach its database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Readiness check failed: database unavailable")
        raise HTTPException(
            status_code=503, detail="database unavailable"
        ) from exc
    if settings.GCS_BUCKET.strip() and not content_artifacts_ready:
        raise HTTPException(
            status_code=503, detail="content recommender artifacts unavailable"
        )
    return {
        "status": "ok",
        "content_recommender": "ready" if content_artifacts_ready else "not_configured",
    }


@app.get("/health/live")
def liveness():
    """Cheap liveness probe; deliberately does not wake a sleeping database."""
    return {"status": "alive"}
