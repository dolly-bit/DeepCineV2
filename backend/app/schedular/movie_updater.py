import asyncio

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.movie import Movie
from app.services.tmdb.client import tmdb_get, aclose_client


async def _update_movies_async():
    db: Session = SessionLocal()

    try:
        print("Updating movies from TMDB...")

        for page in range(1, 6):

            data = await tmdb_get("movie/popular", {"page": page})

            for item in data["results"]:

                movie = db.query(Movie).filter(
                    Movie.tmdb_id == item["id"]
                ).first()

                if movie:
                    movie.title = item["title"]
                    movie.original_title = item.get("original_title")
                    movie.overview = item.get("overview")
                    movie.poster_path = item.get("poster_path")
                    movie.backdrop_path = item.get("backdrop_path")
                    movie.vote_average = item.get("vote_average")
                    movie.vote_count = item.get("vote_count")
                    movie.popularity = item.get("popularity")
                    movie.original_language = item.get("original_language")
                    movie.adult = item.get("adult", False)

                else:
                    db.add(
                        Movie(
                            tmdb_id=item["id"],
                            title=item["title"],
                            original_title=item.get("original_title"),
                            overview=item.get("overview"),
                            poster_path=item.get("poster_path"),
                            backdrop_path=item.get("backdrop_path"),
                            vote_average=item.get("vote_average"),
                            vote_count=item.get("vote_count"),
                            popularity=item.get("popularity"),
                            original_language=item.get("original_language"),
                            adult=item.get("adult", False),
                        )
                    )

        db.commit()

        print("Movie database updated successfully.")

    except Exception as e:
        print(e)

    finally:
        db.close()


def update_movies():
    """
    Sync entry point for APScheduler's BackgroundScheduler (which runs jobs
    in a worker thread, not the app's event loop), so it's safe to spin up
    a fresh asyncio event loop here.
    """
    asyncio.run(_update_movies_async())
