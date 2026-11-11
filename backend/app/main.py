import asyncio
import logging

from fastapi import FastAPI
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
from app.schedular.schedular import start_scheduler, stop_scheduler

logger = logging.getLogger("deepcine")

# Existing project startup behavior creates missing tables on boot.
# New Rating/WatchlistItem models are imported above so their tables are registered.
Base.metadata.create_all(bind=engine)

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
    return {"status": "ok"}
