import asyncio
import sys

from app.database.connection import SessionLocal
from app.services.tmdb.movies import import_popular_movies, TMDBAuthError
from app.services.tmdb.client import aclose_client


async def main():
    db = SessionLocal()
    try:
        total = await import_popular_movies(db, pages=5)

        if total == 0:
            print(
                "0 movies imported. If you saw page errors above, check "
                "backend/.env's TMDB_ACCESS_TOKEN. If movies already "
                "existed in the DB from a previous run, that's expected - "
                "nothing new to add."
            )
        else:
            print(f"{total} movies imported successfully.")

    except TMDBAuthError as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)
    finally:
        db.close()
        await aclose_client()


if __name__ == "__main__":
    asyncio.run(main())
