from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai.recommender import recommend_movies
from ai import collaborative

from app.services.ai_recommendation_services import (
    get_personalized_recommendations
)

from app.database.connection import get_db


router = APIRouter(
    prefix="/recommend",
    tags=["Recommendations"],
)


def _serialize_movie(movie):
    return {
        "id": movie.tmdb_id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
            if movie.poster_path
            else None
        ),
        "overview": movie.overview,
        "vote_average": movie.vote_average or 0,
        "release_date": movie.release_date,
    }


# -----------------------------------------
# Content-Based Recommendation
# -----------------------------------------

@router.get("/content")
def content_recommendation(movie_name: str):
    return recommend_movies(movie_name)


# -----------------------------------------
# Collaborative Filtering
# -----------------------------------------

@router.get("/collaborative/{user_id}")
def collaborative_recommendation(
    user_id: int,
    top_k: int = 10
):
    recommendations = collaborative.recommend_for_user(
        user_id,
        top_k=top_k
    )

    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No collaborative-filtering data for this user yet. "
                "Add watch history and retrain the model."
            )
        )

    return [
        _serialize_movie(movie)
        for movie in recommendations
    ]


# -----------------------------------------
# Personalized Recommendation
# -----------------------------------------

@router.get("/personalized/{user_id}")
def personalized_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
):
    movies = get_personalized_recommendations(
        user_id,
        db
    )

    return [
        _serialize_movie(movie)
        for movie in movies
    ]