from sqlalchemy.orm import Session

from app.models.genre import Genre
from app.services.tmdb.client import tmdb_get


async def import_genres(db: Session):
    data = await tmdb_get("genre/movie/list")

    count = 0

    for item in data["genres"]:
        existing = db.query(Genre).filter(
            Genre.tmdb_id == item["id"]
        ).first()

        if existing:
            continue

        genre = Genre(
            tmdb_id=item["id"],
            name=item["name"]
        )

        db.add(genre)
        count += 1

    db.commit()

    return count
