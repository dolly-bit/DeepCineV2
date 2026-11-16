from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models import Movie, WatchlistItem
from app.models.user import User

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


class WatchlistInput(BaseModel):
    tmdb_id: int = Field(gt=0)


@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(WatchlistItem, Movie)
        .join(Movie, WatchlistItem.movie_id == Movie.id)
        .filter(WatchlistItem.user_id == current_user.id)
        .order_by(WatchlistItem.added_at.desc())
        .all()
    )
    return [{
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "poster_url": (
            f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
            if movie.poster_path else None
        ),
        "added_at": item.added_at,
    } for item, movie in rows]


@router.post("/")
def add_to_watchlist(
    payload: WatchlistInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movie = db.query(Movie).filter(Movie.tmdb_id == payload.tmdb_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not in the local catalog.")

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == movie.id,
    ).first()
    if existing:
        return {"added": True, "already_exists": True}

    db.add(WatchlistItem(user_id=current_user.id, movie_id=movie.id))
    db.commit()
    return {"added": True, "already_exists": False}


@router.delete("/{tmdb_id}")
def remove_from_watchlist(
    tmdb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found.")
    deleted = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.movie_id == movie.id,
    ).delete(synchronize_session=False)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Movie is not in your watchlist.")
    return {"removed": True}
