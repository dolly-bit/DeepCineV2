from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    Date
)

from app.database.connection import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)

    tmdb_id = Column(Integer, unique=True, nullable=False)

    imdb_id = Column(String(20), nullable=True)

    title = Column(String(300), nullable=False)

    original_title = Column(String(300))

    overview = Column(Text)

    poster_path = Column(String(500))

    backdrop_path = Column(String(500))

    release_date = Column(Date)

    runtime = Column(Integer)

    vote_average = Column(Float)

    vote_count = Column(Integer)

    popularity = Column(Float)

    original_language = Column(String(10))

    adult = Column(Boolean, default=False)

    status = Column(String(50))

    tagline = Column(Text)