import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models import Movie, Rating, User, WatchHistory, WatchlistItem
from app.services.co_watch_recommendations import get_co_watch_recommendations


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def user(db, suffix):
    item = User(username=f"user-{suffix}", email=f"user-{suffix}@example.com", hashed_password="x")
    db.add(item)
    db.flush()
    return item


def movie(db, tmdb_id):
    item = Movie(tmdb_id=tmdb_id, title=f"Movie {tmdb_id}")
    db.add(item)
    db.flush()
    return item


def test_co_watch_uses_distinct_viewer_movie_pairs_and_cosine_score(db):
    target = user(db, "target")
    viewer_a, viewer_b = user(db, "a"), user(db, "b")
    seed, candidate = movie(db, 100), movie(db, 200)
    db.add_all([
        WatchHistory(user_id=target.id, tmdb_id=seed.tmdb_id),
        WatchHistory(user_id=viewer_a.id, tmdb_id=seed.tmdb_id),
        WatchHistory(user_id=viewer_a.id, tmdb_id=candidate.tmdb_id),
        WatchHistory(user_id=viewer_a.id, tmdb_id=candidate.tmdb_id),
        WatchHistory(user_id=viewer_b.id, tmdb_id=seed.tmdb_id),
        WatchHistory(user_id=viewer_b.id, tmdb_id=candidate.tmdb_id),
    ])
    db.commit()

    results = get_co_watch_recommendations(target.id, db)
    assert len(results) == 1
    assert results[0][0].tmdb_id == 200
    assert results[0][1] == pytest.approx(1.0)
    assert results[0][2] == 2


def test_co_watch_excludes_seed_rated_and_watchlisted_movies(db):
    target, viewer = user(db, "target2"), user(db, "viewer2")
    seed, rated, saved, candidate = [movie(db, mid) for mid in (101, 102, 103, 104)]
    db.add_all([
        WatchHistory(user_id=target.id, tmdb_id=seed.tmdb_id),
        Rating(user_id=target.id, movie_id=rated.id, value=5),
        WatchlistItem(user_id=target.id, movie_id=saved.id),
        *[WatchHistory(user_id=viewer.id, tmdb_id=mid) for mid in (101, 102, 103, 104)],
    ])
    db.commit()

    results = get_co_watch_recommendations(target.id, db)
    assert [row[0].tmdb_id for row in results] == [104]


def test_co_watch_minimum_support_and_empty_history(db):
    target, viewer = user(db, "target3"), user(db, "viewer3")
    seed, candidate = movie(db, 301), movie(db, 302)
    db.add_all([
        WatchHistory(user_id=target.id, tmdb_id=seed.tmdb_id),
        WatchHistory(user_id=viewer.id, tmdb_id=seed.tmdb_id),
        WatchHistory(user_id=viewer.id, tmdb_id=candidate.tmdb_id),
    ])
    db.commit()

    assert get_co_watch_recommendations(target.id, db, min_shared_users=2) == []
    assert get_co_watch_recommendations(99999, db) == []
