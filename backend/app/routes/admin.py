"""
HTTP-triggered admin tasks - seeding the catalog and rebuilding the
recommendation index, without needing shell/SSH access to the server.

Render's free tier doesn't include shell access, so `python
import_movies.py` etc. can't be run directly against a deployed free
instance. These endpoints run the exact same underlying functions, but
triggered by a plain HTTP request instead - works on any hosting tier.

Protected by a shared-secret token (ADMIN_TASK_TOKEN) rather than normal
user auth, since this needs to be callable by an operator (you), not a
logged-in end user, and it's fine for it to work even before any user
account exists.
"""

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.services.tmdb.movies import import_catalog_movies, TMDBAuthError
from app.services.tmdb.genres import import_genres
from app.services.tmdb.genres import import_genres
from ai.index_builder import build_recommendation_index
from ai.recommender import invalidate_index_cache
from app.services.tmdb.client import TMDB_CACHE

router = APIRouter(prefix="/admin", tags=["Admin"])


def _check_token(x_admin_token: str | None):
    if not settings.ADMIN_TASK_TOKEN:
        raise HTTPException(
            status_code=503,
            detail=(
                "ADMIN_TASK_TOKEN is not set on the server, so these "
                "endpoints are disabled. Set it in your environment "
                "variables (any long random string), redeploy, then "
                "call this endpoint again with the same value in the "
                "X-Admin-Token header."
            ),
        )

    if not x_admin_token or x_admin_token != settings.ADMIN_TASK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token header.")


@router.post("/seed")
async def seed_database(x_admin_token: str | None = Header(default=None)):
    """
    Imports up to 10,000 TMDB discover results with genre links, then builds the recommendation index. Equivalent to running all four local scripts
    in order, but over HTTP.

    Usage (replace with your real values):
        curl -X POST https://your-api.onrender.com/admin/seed \\
             -H "X-Admin-Token: <your ADMIN_TASK_TOKEN>"

    Safe to rerun - existing TMDB IDs are updated rather than duplicated.
    """
    _check_token(x_admin_token)

    db: Session = SessionLocal()
    result = {}

    try:
        try:
            await import_genres(db)
            result.update(await import_catalog_movies(db, target_count=10_000))
        except TMDBAuthError as e:
            raise HTTPException(status_code=502, detail=str(e))

        # Rebuild the recommendation index and invalidate in-memory caches
        indexed = build_recommendation_index(db, verbose=False)
        result["movies_indexed"] = indexed

        invalidate_index_cache()
        TMDB_CACHE.clear()

        result["status"] = "done"
        return result

    finally:
        db.close()


@router.post("/refresh-index")
async def refresh_index_only(x_admin_token: str | None = Header(default=None)):
    """
    Lighter-weight than /admin/seed: just rebuilds the recommendation
    index from whatever's currently in the DB, without re-hitting TMDB.
    Useful after the daily auto-update job runs (which already does this
    itself) if you ever need to force it manually - e.g. right after a
    redeploy, since the index file doesn't survive Render's ephemeral
    filesystem across deploys.
    """
    _check_token(x_admin_token)

    db: Session = SessionLocal()
    try:
        indexed = build_recommendation_index(db, verbose=False)
        invalidate_index_cache()
        return {"movies_indexed": indexed, "status": "done"}
    finally:
        db.close()