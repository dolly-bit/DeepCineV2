from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models import WatchHistory
from app.models.user import User

router = APIRouter(prefix="/watch-history", tags=["Watch History"])


@router.post("/")
def add_watch_history(
    tmdb_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = WatchHistory(user_id=current_user.id, tmdb_id=tmdb_id)
    db.add(history)
    db.commit()
    return {"message": "Watch history saved"}


@router.get("/stats")
def get_watch_history_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WatchHistory).filter(
        WatchHistory.user_id == current_user.id
    )
    total = query.count()
    unique_movies = db.query(WatchHistory.tmdb_id).filter(
        WatchHistory.user_id == current_user.id
    ).distinct().count()
    return {
        "total_watch_history_records": total,
        "unique_users": 1 if total else 0,
        "unique_movies": unique_movies,
    }
