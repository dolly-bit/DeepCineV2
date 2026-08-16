import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.tmdb.movies import (
    get_trending_movies,
    get_top_rated_movies,
    get_upcoming_movies,
    search_movies,
)
from app.services.tmdb.details import tmdb_get
from app.services.tmdb.discover import (
    discover_movies,
    list_moods,
    LANGUAGES,
    GENRE_IDS,
)
from app.services.ai_recommendation_services import get_personalized_recommendations

router = APIRouter(prefix="/movies", tags=["Movies"])


def format_movies(movies):
    formatted = []

    for movie in movies:
        formatted.append({
            "id": movie.get("id"),
            "title": movie.get("title"),
            "overview": movie.get("overview"),
            "poster_url": (
                f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                if movie.get("poster_path")
                else None
            ),
            "backdrop_url": (
                f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}"
                if movie.get("backdrop_path")
                else None
            ),
            "release_date": movie.get("release_date"),
            "vote_average": movie.get("vote_average"),
        })

    return formatted


def _serialize_db_movie(movie):
    """Serialize a Movie ORM row (used by the personalized/recommended
    endpoint, which reads from our own DB rather than live TMDB JSON)."""
    return {
        "id": movie.tmdb_id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
            if movie.poster_path
            else None
        ),
        "backdrop_url": (
            f"https://image.tmdb.org/t/p/original{movie.backdrop_path}"
            if movie.backdrop_path
            else None
        ),
        "overview": movie.overview,
        "vote_average": movie.vote_average or 0,
        "release_date": movie.release_date,
    }


@router.get("/trending")
async def trending_movies():
    try:
        results = await get_trending_movies()
        return format_movies(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-rated")
async def top_rated_movies():
    try:
        results = await get_top_rated_movies()
        return format_movies(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def upcoming_movies():
    try:
        results = await get_upcoming_movies()
        today = datetime.date.today()
        future_movies = []

        for movie in results:
            release_date = movie.get("release_date")
            if not release_date:
                continue

            try:
                release_dt = datetime.date.fromisoformat(release_date)
            except ValueError:
                continue

            if release_dt >= today:
                future_movies.append(movie)

        future_movies.sort(key=lambda movie: movie.get("release_date") or "")
        return format_movies(future_movies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(query: str):
    try:
        results = await search_movies(query)
        return format_movies(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: This static route must be declared before the dynamic
# "/{movie_id}" route below, otherwise FastAPI would try to match
# "recommended" as a movie_id and 422 on every call.
@router.get("/recommended/{user_id}")
def recommended_movies(
    user_id: int,
    db: Session = Depends(get_db),
):
    movies = get_personalized_recommendations(user_id, db)
    return [_serialize_db_movie(movie) for movie in movies]


@router.get("/moods")
def get_moods():
    """Returns the list of browsable moods, for building filter UI."""
    return list_moods()


@router.get("/genres")
def get_genres():
    """Returns the list of browsable genres (name + TMDB id), for
    building filter UI."""
    return [{"id": gid, "name": name.replace("_", " ").title()} for name, gid in GENRE_IDS.items()]


@router.get("/languages")
def get_languages():
    """Returns the curated list of browsable languages."""
    return LANGUAGES


@router.get("/discover")
async def discover(
    genres: Optional[str] = None,
    language: Optional[str] = None,
    mood: Optional[str] = None,
    sort_by: str = "popularity.desc",
    page: int = 1,
):
    """
    Browse movies by any combination of mood / genre / language.

    - `genres`: comma-separated TMDB genre IDs, e.g. "28,12"
    - `language`: ISO 639-1 code, e.g. "hi", "ko", "en"
    - `mood`: one of the keys from GET /movies/moods, e.g. "feel_good"
    - `sort_by`: TMDB sort key, e.g. "popularity.desc", "vote_average.desc"

    All filters are optional and combine together (e.g. mood=scary &
    language=ko returns scary Korean movies). If nothing is passed,
    behaves like a generic popularity-sorted discover feed.
    """
    try:
        genre_ids = (
            [int(g) for g in genres.split(",") if g.strip()]
            if genres
            else None
        )

        results = await discover_movies(
            genres=genre_ids,
            language=language,
            mood=mood,
            sort_by=sort_by,
            page=page,
        )

        return format_movies(results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{movie_id}")
async def get_movie_details(movie_id: int):
    try:
        movie = await tmdb_get(f"movie/{movie_id}")

        return {
            "id": movie.get("id"),
            "title": movie.get("title"),
            "overview": movie.get("overview"),
            "poster_url": (
                f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                if movie.get("poster_path")
                else None
            ),
            "backdrop_url": (
                f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}"
                if movie.get("backdrop_path")
                else None
            ),
            "release_date": movie.get("release_date"),
            "vote_average": movie.get("vote_average"),
            "runtime": movie.get("runtime"),
            "genres": movie.get("genres", []),
            "tagline": movie.get("tagline"),
            "status": movie.get("status"),
            "homepage": movie.get("homepage"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{movie_id}/trailer")
async def get_movie_trailer(movie_id: int):
    try:
        data = await tmdb_get(f"movie/{movie_id}/videos")

        videos = data.get("results", [])

        trailer = next(
            (
                video
                for video in videos
                if video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
            ),
            None,
        )

        if not trailer:
            return {"url": None}

        return {
            "url": f"https://www.youtube.com/watch?v={trailer['key']}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{movie_id}/cast")
async def get_movie_cast(movie_id: int):
    try:
        data = await tmdb_get(f"movie/{movie_id}/credits")

        cast = []

        for actor in data.get("cast", [])[:10]:
            cast.append({
                "id": actor.get("id"),
                "name": actor.get("name"),
                "character": actor.get("character"),
                "profile_url": (
                    f"https://image.tmdb.org/t/p/w300{actor['profile_path']}"
                    if actor.get("profile_path")
                    else None
                ),
            })

        return cast

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{movie_id}/similar")
async def get_similar_movies(movie_id: int):
    try:
        data = await tmdb_get(f"movie/{movie_id}/similar")

        # TMDB's "similar" algorithm sometimes surfaces obscure entries
        # with no poster and no votes (e.g. "Domestic Appliances"-style
        # junk data) mixed in among genuinely similar movies. Filtering
        # BEFORE slicing to 10 - instead of after - means those don't
        # crowd out better matches further down the raw list.
        candidates = [
            movie
            for movie in data.get("results", [])
            if movie.get("poster_path") and movie.get("vote_count", 0) > 0
        ]

        movies = []

        for movie in candidates[:10]:
            movies.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "poster_url": (
                    f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                    if movie.get("poster_path")
                    else None
                ),
                "vote_average": movie.get("vote_average"),
                "release_date": movie.get("release_date"),
            })

        return movies

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))