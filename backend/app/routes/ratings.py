from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models import Movie, Rating
from app.models.user import User

router = APIRouter(prefix="/ratings", tags=["Ratings"])


class RatingInput(BaseModel):
    tmdb_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)


@router.put("/")
def upsert_rating(
    payload: RatingInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movie = db.query(Movie).filter(Movie.tmdb_id == payload.tmdb_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not in the local catalog.")

    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie.id,
    ).first()
    if rating is None:
        rating = Rating(
            user_id=current_user.id,
            movie_id=movie.id,
            value=payload.rating,
        )
        db.add(rating)
    else:
        rating.value = payload.rating
        rating.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(rating)
    return {
        "tmdb_id": movie.tmdb_id,
        "rating": rating.value,
        "updated_at": rating.updated_at,
    }


@router.get("/mine")
def get_my_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Rating, Movie)
        .join(Movie, Rating.movie_id == Movie.id)
        .filter(Rating.user_id == current_user.id)
        .order_by(Rating.updated_at.desc())
        .all()
    )
    return [{
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "rating": rating.value,
        "updated_at": rating.updated_at,
    } for rating, movie in rows]


@router.delete("/{tmdb_id}")
def delete_rating(
    tmdb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found.")
    deleted = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie.id,
    ).delete(synchronize_session=False)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Rating not found.")
    return {"deleted": True}
