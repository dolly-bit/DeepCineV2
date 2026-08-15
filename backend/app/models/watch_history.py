from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    tmdb_id = Column(
        Integer,
        nullable=False
    )

    watched_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship("User")