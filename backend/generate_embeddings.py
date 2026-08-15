"""
Builds the content-based recommendation index from scratch.

Run this after importing movies (import_movies.py) - and re-run it any
time your local movie catalog changes, so the index stays in sync with
what's actually in your database. (The daily auto-update job does this
automatically - see app/schedular/movie_updater.py.)
"""

from app.database.connection import SessionLocal
from ai.index_builder import build_recommendation_index


def main():
    db = SessionLocal()
    try:
        build_recommendation_index(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
