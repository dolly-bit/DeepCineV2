from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ai.recommender import recommend_movies
from ai import collaborative
from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.services.co_watch_recommendations import get_co_watch_recommendations
from app.services.ai_recommendation_services import (
    get_personalized_recommendations,
    build_recommendation_explanations,
)

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


def _require_self(user_id: int, current_user: User):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access recommendations for your own account.",
        )


def _serialize_movie(movie, recommendation_reason=None):
    return {
        "id": movie.tmdb_id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
            if movie.poster_path else None
        ),
        "overview": movie.overview,
        "vote_average": movie.vote_average or 0,
        "release_date": movie.release_date,
        "recommendation_reason": recommendation_reason,
    }


@router.get("/content")
def content_recommendation(movie_name: str):
    return recommend_movies(movie_name)


@router.get("/collaborative/{user_id}")
def collaborative_recommendation(
    user_id: int,
    top_k: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    _require_self(user_id, current_user)
    recommendations = collaborative.recommend_for_user(user_id, top_k=top_k)
    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail="No collaborative-filtering model is available yet.",
        )
    return [_serialize_movie(movie) for movie in recommendations]


@router.get("/personalized/{user_id}")
def personalized_recommendations(
    user_id: int,
    top_k: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_self(user_id, current_user)
    movies = get_personalized_recommendations(user_id, db, top_k=top_k)
    explanations = build_recommendation_explanations(user_id, movies, db)
    return [
        _serialize_movie(movie, explanations.get(movie.tmdb_id))
        for movie in movies
    ]


@router.get("/co-watch/{user_id}")
def co_watch_recommendations(
    user_id: int,
    top_k: int = Query(default=20, ge=1, le=50),
    min_shared_users: int = Query(default=1, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_self(user_id, current_user)
    results = get_co_watch_recommendations(
        user_id, db, top_k=top_k, min_shared_users=min_shared_users
    )
    return [
        _serialize_movie(
            movie,
            f"Explored by {shared} other viewer(s) who also explored films in your history.",
        ) | {"co_watch_score": round(score, 4), "shared_viewers": shared}
        for movie, score, shared in results
    ]
