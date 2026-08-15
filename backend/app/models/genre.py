from sqlalchemy import Column, Integer, String
from app.database.connection import Base


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)