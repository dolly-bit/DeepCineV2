import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.database.connection import get_db
from app.services.tmdb.movies import (
    get_trending_movies, get_top_rated_movies, get_upcoming_movies, search_movies,
)
from app.services.tmdb.details import tmdb_get
from app.services.tmdb.discover import (
    discover_movies, list_moods, LANGUAGES, GENRE_IDS,
)
from app.services.ai_recommendation_services import get_personalized_recommendations

router = APIRouter(prefix="/movies", tags=["Movies"])


def format_movies(movies):
    return [{
        "id": movie.get("id"),
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            if movie.get("poster_path") else None
        ),
        "backdrop_url": (
            f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}"
            if movie.get("backdrop_path") else None
        ),
        "release_date": movie.get("release_date"),
        "vote_average": movie.get("vote_average"),
    } for movie in movies]


def _serialize_db_movie(movie):
    return {
        "id": movie.tmdb_id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
            if movie.poster_path else None
        ),
        "backdrop_url": (
            f"https://image.tmdb.org/t/p/original{movie.backdrop_path}"
            if movie.backdrop_path else None
        ),
        "overview": movie.overview,
        "vote_average": movie.vote_average or 0,
        "release_date": movie.release_date,
    }


@router.get("/trending")
async def trending_movies():
    try:
        return format_movies(await get_trending_movies())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/top-rated")
async def top_rated_movies():
    try:
        return format_movies(await get_top_rated_movies())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/upcoming")
async def upcoming_movies():
    try:
        results = await get_upcoming_movies()
        today = datetime.date.today()
        future = []
        for movie in results:
            value = movie.get("release_date")
            if not value:
                continue
            try:
                release_date = datetime.date.fromisoformat(value)
            except ValueError:
                continue
            if release_date >= today:
                future.append(movie)
        future.sort(key=lambda movie: movie.get("release_date") or "")
        return format_movies(future)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/search")
async def search(query: str):
    try:
        return format_movies(await search_movies(query))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recommended/{user_id}")
def recommended_movies(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own recommendations.")
    movies = get_personalized_recommendations(user_id, db)
    return [_serialize_db_movie(movie) for movie in movies]


@router.get("/moods")
def get_moods():
    return list_moods()


@router.get("/genres")
def get_genres():
    return [{"id": gid, "name": name.replace("_", " ").title()} for name, gid in GENRE_IDS.items()]


@router.get("/languages")
def get_languages():
    return LANGUAGES


@router.get("/discover")
async def discover(
    genres: Optional[str] = None,
    language: Optional[str] = None,
    mood: Optional[str] = None,
    sort_by: str = "popularity.desc",
    page: int = 1,
):
    try:
        genre_ids = [int(g) for g in genres.split(",") if g.strip()] if genres else None
        results = await discover_movies(
            genres=genre_ids, language=language, mood=mood,
            sort_by=sort_by, page=page,
        )
        return format_movies(results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
                if movie.get("poster_path") else None
            ),
            "backdrop_url": (
                f"https://image.tmdb.org/t/p/original{movie['backdrop_path']}"
                if movie.get("backdrop_path") else None
            ),
            "release_date": movie.get("release_date"),
            "vote_average": movie.get("vote_average"),
            "runtime": movie.get("runtime"),
            "genres": movie.get("genres", []),
            "tagline": movie.get("tagline"),
            "status": movie.get("status"),
            "homepage": movie.get("homepage"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{movie_id}/trailer")
async def get_movie_trailer(movie_id: int):
    try:
        videos = (await tmdb_get(f"movie/{movie_id}/videos")).get("results", [])
        trailer = next((
            video for video in videos
            if video.get("site") == "YouTube" and video.get("type") == "Trailer"
        ), None)
        return {"url": f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else None}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{movie_id}/cast")
async def get_movie_cast(movie_id: int):
    try:
        data = await tmdb_get(f"movie/{movie_id}/credits")
        return [{
            "id": actor.get("id"),
            "name": actor.get("name"),
            "character": actor.get("character"),
            "profile_url": (
                f"https://image.tmdb.org/t/p/w300{actor['profile_path']}"
                if actor.get("profile_path") else None
            ),
        } for actor in data.get("cast", [])[:10]]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{movie_id}/similar")
async def get_similar_movies(movie_id: int):
    try:
        data = await tmdb_get(f"movie/{movie_id}/similar")
        candidates = [
            movie for movie in data.get("results", [])
            if movie.get("poster_path") and movie.get("vote_count", 0) > 0
        ]
        return [{
            "id": movie.get("id"),
            "title": movie.get("title"),
            "poster_url": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
            "vote_average": movie.get("vote_average"),
            "release_date": movie.get("release_date"),
        } for movie in candidates[:10]]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
