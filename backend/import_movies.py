import asyncio
import sys

from app.database.connection import SessionLocal
from app.services.tmdb.movies import import_catalog_movies, TMDBAuthError
from app.services.tmdb.client import aclose_client

TARGET_MOVIES = 10_000


async def main():
    db = SessionLocal()
    try:
        result = await import_catalog_movies(db, target_count=TARGET_MOVIES)
        print("\nCatalog import summary:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        if not result["target_reached"]:
            print(
                "\nThe target was not reached in this run. Check failed pages "
                "and rerun; imported records are retained and duplicates avoided."
            )
        print(
            "\nNext, run: python generate_embeddings.py "
            "\nThen run: python link_movie_genres.py only if you have older "
            "records without genre links."
        )
    except TMDBAuthError as exc:
        print(f"\n[ERROR] {exc}\n")
        sys.exit(1)
    finally:
        db.close()
        await aclose_client()


if __name__ == "__main__":
    asyncio.run(main())
