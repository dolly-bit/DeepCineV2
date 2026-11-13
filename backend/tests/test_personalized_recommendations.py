import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models import (
    Genre,
    Movie,
    MovieGenre,
    Rating,
    User,
    WatchHistory,
    WatchlistItem,
)
from app.services import ai_recommendation_services as recommendation_service


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def add_movie(db, tmdb_id, title):
    movie = Movie(tmdb_id=tmdb_id, title=title)
    db.add(movie)
    db.flush()
    return movie


def seed_interactions(db):
    user = User(
        username="recommendation-test",
        email="recommendation-test@example.com",
        hashed_password="not-a-real-password",
    )
    db.add(user)
    db.flush()

    watched = add_movie(db, 101, "Already Watched")
    disliked = add_movie(db, 102, "Previously Disliked")
    saved = add_movie(db, 103, "Saved for Later")
    candidate_a = add_movie(db, 104, "Candidate A")
    candidate_b = add_movie(db, 105, "Candidate B")

    db.add(WatchHistory(user_id=user.id, tmdb_id=watched.tmdb_id))
    db.add(Rating(user_id=user.id, movie_id=disliked.id, value=1))
    db.add(WatchlistItem(user_id=user.id, movie_id=saved.id))
    db.commit()

    return user, [watched, disliked, saved, candidate_a, candidate_b]


def test_interacted_movies_are_removed_before_rank_fusion(db_session, monkeypatch):
    user, movies = seed_interactions(db_session)
    raw_candidates = [movie.tmdb_id for movie in movies]

    monkeypatch.setattr(
        recommendation_service,
        "recommend_for_user_content",
        lambda *_args, **_kwargs: raw_candidates,
    )
    monkeypatch.setattr(
        recommendation_service.collaborative,
        "recommendation_scores_for_user",
        lambda *_args, **_kwargs: [(tmdb_id, 1.0) for tmdb_id in raw_candidates],
    )

    captured_rankings = {}

    def capture_fusion(rankings, weights=None, top_k=20, **_kwargs):
        captured_rankings.update(rankings)
        # Return the first eligible IDs from the content ranking.
        return rankings["content"][:top_k]

    monkeypatch.setattr(
        recommendation_service,
        "reciprocal_rank_fusion",
        capture_fusion,
    )

    results = recommendation_service.get_personalized_recommendations(
        user.id, db_session, top_k=2
    )

    assert captured_rankings["content"] == [104, 105]
    assert captured_rankings["collaborative"] == [104, 105]
    assert [movie.tmdb_id for movie in results] == [104, 105]


def test_recommendations_do_not_return_watched_disliked_or_saved_movies(
    db_session, monkeypatch
):
    user, movies = seed_interactions(db_session)
    raw_candidates = [movie.tmdb_id for movie in movies]

    monkeypatch.setattr(
        recommendation_service,
        "recommend_for_user_content",
        lambda *_args, **_kwargs: raw_candidates,
    )
    monkeypatch.setattr(
        recommendation_service.collaborative,
        "recommendation_scores_for_user",
        lambda *_args, **_kwargs: [(tmdb_id, 1.0) for tmdb_id in raw_candidates],
    )

    results = recommendation_service.get_personalized_recommendations(
        user.id, db_session, top_k=5
    )

    result_ids = {movie.tmdb_id for movie in results}
    assert result_ids.isdisjoint({101, 102, 103})
    assert result_ids == {104, 105}
