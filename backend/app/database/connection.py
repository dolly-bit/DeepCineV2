from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings


connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

pool_mode = settings.DB_POOL_MODE.strip().lower()
if pool_mode not in {"queue", "null"}:
    raise ValueError("DB_POOL_MODE must be either 'queue' or 'null'")

engine_options = {
    "connect_args": connect_args,
}

if pool_mode == "null":
    # Serverless PostgreSQL providers suspend only after connections close.
    # NullPool closes the DBAPI connection when a SQLAlchemy connection is
    # returned, avoiding idle connections held by this API process.
    engine_options["poolclass"] = NullPool
else:
    engine_options["pool_pre_ping"] = True

engine = create_engine(settings.DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
