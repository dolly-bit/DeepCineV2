from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models import SearchHistory
from app.models.user import User

router = APIRouter(prefix="/search-history", tags=["Search History"])


@router.post("/")
def save_search(
    query: str = Query(..., min_length=1, max_length=300),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = SearchHistory(user_id=current_user.id, query=query.strip())
    db.add(history)
    db.commit()
    return {"message": "Search saved"}
