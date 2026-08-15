from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import SearchHistory

router = APIRouter(
    prefix="/search-history",
    tags=["Search History"]
)


@router.post("/")
def save_search(
    user_id: int,
    query: str,
    db: Session = Depends(get_db)
):
    history = SearchHistory(
        user_id=user_id,
        query=query
    )

    db.add(history)
    db.commit()

    return {
        "message": "Search saved"
    }