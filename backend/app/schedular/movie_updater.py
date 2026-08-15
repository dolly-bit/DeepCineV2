import asyncio

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.services.tmdb.movies import import_popular_movies, TMDBAuthError
from app.services.tmdb.client import aclose_client, TMDB_CACHE
from ai.index_builder import build_recommendation_index
from ai.recommender import invalidate_index_cache


async def _update_movies_async():
    """
    The daily auto-update pipeline:
      1. Re-fetch TMDB's popular list (500 movies) - adds anything new,
         refreshes ratings/popularity on everything already imported.
      2. Rebuild the content-recommendation index so new movies are
         actually recommendable, not just sitting in the DB unused.
      3. Invalidate in-memory caches (the FAISS index this server
         process has cached, and the TMDB trending/top-rated/upcoming
         cache) so the changes take effect immediately instead of
         waiting for a restart or a TTL to expire.
    """
    db: Session = SessionLocal()

    try:
        print("[auto-update] Refreshing movie catalog from TMDB...")
        new_count = await import_popular_movies(db, pages=25)
        print(f"[auto-update] {new_count} new movies added.")

        print("[auto-update] Rebuilding recommendation index...")
        indexed = build_recommendation_index(db, verbose=False)
        print(f"[auto-update] Recommendation index rebuilt ({indexed} movies).")

        invalidate_index_cache()
        TMDB_CACHE.clear()

        print("[auto-update] Done - catalog and recommendations are fresh.")

    except TMDBAuthError as e:
        print(f"[auto-update] Skipped: {e}")

    except Exception as e:
        print(f"[auto-update] Failed: {e}")

    finally:
        db.close()
        await aclose_client()


def update_movies():
    """
    Sync entry point for APScheduler's BackgroundScheduler (which runs jobs
    in a worker thread, not the app's event loop), so it's safe to spin up
    a fresh asyncio event loop here.
    """
    asyncio.run(_update_movies_async())
