import asyncio

from app.database.connection import SessionLocal
from app.services.tmdb.genres import import_genres
from app.services.tmdb.client import aclose_client


async def main():
    db = SessionLocal()
    try:
        total = await import_genres(db)
        print(f"{total} genres imported successfully.")
    finally:
        db.close()
        await aclose_client()


if __name__ == "__main__":
    asyncio.run(main())
