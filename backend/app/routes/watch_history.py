from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import WatchHistory

router = APIRouter(
    prefix="/watch-history",
    tags=["Watch History"]
)


@router.post("/")
def add_watch_history(
    user_id: int,
    tmdb_id: int,
    db: Session = Depends(get_db)
):
    history = WatchHistory(
        user_id=user_id,
        tmdb_id=tmdb_id,
    )

    db.add(history)
    db.commit()

    return {
        "message": "Watch history saved"
    }


@router.get("/stats")
def get_watch_history_stats(
    db: Session = Depends(get_db)
):
    total_records = db.query(WatchHistory).count()

    unique_users = (
        db.query(WatchHistory.user_id)
        .distinct()
        .count()
    )

    unique_movies = (
        db.query(WatchHistory.tmdb_id)
        .distinct()
        .count()
    )

    return {
        "total_watch_history_records": total_records,
        "unique_users": unique_users,
        "unique_movies": unique_movies,
    }