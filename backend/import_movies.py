import asyncio
import sys

from app.database.connection import SessionLocal
from app.services.tmdb.movies import import_popular_movies, TMDBAuthError
from app.services.tmdb.client import aclose_client

# 25 pages x 20 movies/page = up to 500 movies.
PAGES = 25


async def main():
    db = SessionLocal()
    try:
        new_count = await import_popular_movies(db, pages=PAGES)

        if new_count == 0:
            print(
                "0 new movies. If you saw page errors above, check "
                "backend/.env's TMDB_ACCESS_TOKEN. Otherwise this is "
                "expected if you already imported recently - TMDB's "
                "popular list doesn't change much day to day, so a repeat "
                "run mostly just refreshes existing movies' ratings "
                "(see 'Refreshed stats for N already-imported movies' "
                "above) rather than adding new ones."
            )
        else:
            print(f"{new_count} new movies imported successfully.")

        print(
            "\nRun `python generate_embeddings.py` next so new movies are "
            "included in content-based recommendations."
        )

    except TMDBAuthError as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)
    finally:
        db.close()
        await aclose_client()


if __name__ == "__main__":
    asyncio.run(main())
