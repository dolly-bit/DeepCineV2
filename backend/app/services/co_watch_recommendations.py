from collections import defaultdict
from math import sqrt

from sqlalchemy.orm import Session

from app.models import Movie, Rating, WatchHistory, WatchlistItem


def get_co_watch_recommendations(user_id: int, db: Session, top_k: int = 20, min_shared_users: int = 1):
    """Rank unseen movies explored by users who also explored this user's movies.

    Counts distinct user/movie pairs so repeated movie-detail page opens do not
    inflate support. The score is cosine-style overlap between viewer sets.
    """
    if top_k <= 0 or min_shared_users <= 0:
        return []

    seed_ids = {
        row[0] for row in db.query(WatchHistory.tmdb_id)
        .filter(WatchHistory.user_id == user_id).distinct().all()
    }
    if not seed_ids:
        return []

    excluded = set(seed_ids)
    rated_db_ids = {
        row[0] for row in db.query(Rating.movie_id)
        .filter(Rating.user_id == user_id).all()
    }
    saved_db_ids = {
        row[0] for row in db.query(WatchlistItem.movie_id)
        .filter(WatchlistItem.user_id == user_id).all()
    }
    feedback_db_ids = rated_db_ids | saved_db_ids
    if feedback_db_ids:
        excluded.update(
            row[0] for row in db.query(Movie.tmdb_id)
            .filter(Movie.id.in_(feedback_db_ids)).all()
        )

    interactions = db.query(WatchHistory.user_id, WatchHistory.tmdb_id).filter(
        WatchHistory.user_id != user_id
    ).distinct().all()

    seed_viewers = set()
    candidate_viewers = defaultdict(set)
    for viewer_id, tmdb_id in interactions:
        if tmdb_id in seed_ids:
            seed_viewers.add(viewer_id)
        else:
            candidate_viewers[tmdb_id].add(viewer_id)

    if not seed_viewers:
        return []

    ranked = []
    for tmdb_id, viewers in candidate_viewers.items():
        shared = viewers & seed_viewers
        if tmdb_id in excluded or len(shared) < min_shared_users:
            continue
        score = len(shared) / sqrt(len(seed_viewers) * len(viewers))
        ranked.append((tmdb_id, score, len(shared)))

    ranked.sort(key=lambda item: (-item[1], -item[2], item[0]))
    ranked = ranked[:top_k]
    if not ranked:
        return []

    movies = db.query(Movie).filter(
        Movie.tmdb_id.in_([item[0] for item in ranked])
    ).all()
    by_id = {movie.tmdb_id: movie for movie in movies}
    return [
        (by_id[tmdb_id], score, shared)
        for tmdb_id, score, shared in ranked if tmdb_id in by_id
    ]
