from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database.connection import Base


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    id = Column(Integer, primary_key=True)

    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    genre_id = Column(Integer, ForeignKey("genres.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("movie_id", "genre_id", name="uq_movie_genre"),
    )