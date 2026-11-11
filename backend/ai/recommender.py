import numpy as np
from pathlib import Path

from app.database.connection import SessionLocal
from app.models.movie import Movie
from app.models.watch_history import WatchHistory

BASE_DIR = Path(__file__).resolve().parent.parent
_model = None
_index = None
_movie_ids = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_index_and_ids():
    global _index, _movie_ids
    if _index is None:
        import faiss
        _index = faiss.read_index(str(BASE_DIR / "movie_index.faiss"))
        _movie_ids = np.load(str(BASE_DIR / "movie_ids.npy"))
    return _index, _movie_ids


def invalidate_index_cache():
    global _index, _movie_ids
    _index = None
    _movie_ids = None


def _movie_text(movie):
    return (
        f"Title: {movie.title}\n"
        f"Overview: {movie.overview or ''}\n"
        f"Language: {movie.original_language or ''}"
    )


def recommend_movies(movie_name: str, top_k: int = 10):
    """Existing title-to-title content recommendation contract."""
    db = SessionLocal()
    try:
        movie = db.query(Movie).filter(
            Movie.title.ilike(f"%{movie_name}%")
        ).first()
        if not movie:
            return []

        model = get_model()
        index, movie_ids = _get_index_and_ids()
        embedding = model.encode([_movie_text(movie)]).astype("float32")
        _, indices = index.search(embedding, top_k + 1)
        results = []

        for idx in indices[0]:
            if idx < 0 or idx >= len(movie_ids):
                continue
            movie_id = int(movie_ids[idx])
            if movie_id == movie.id:
                continue
            candidate = db.query(Movie).filter(Movie.id == movie_id).first()
            if candidate:
                results.append({
                    "id": candidate.id,
                    "title": candidate.title,
                    "poster_url": (
                        f"https://image.tmdb.org/t/p/w500{candidate.poster_path}"
                        if candidate.poster_path else None
                    ),
                    "overview": candidate.overview,
                    "rating": candidate.vote_average,
                    "release_date": candidate.release_date,
                })
        return results[:top_k]
    finally:
        db.close()


def recommend_for_user_content(user_id: int, db, top_k: int = 100):
    """Return TMDB IDs ranked by semantic proximity to a user's watch history."""
    if top_k <= 0:
        return []
    index_path = BASE_DIR / "movie_index.faiss"
    ids_path = BASE_DIR / "movie_ids.npy"
    if not index_path.exists() or not ids_path.exists():
        return []

    watched_ids = {
        row[0] for row in db.query(WatchHistory.tmdb_id)
        .filter(WatchHistory.user_id == user_id).distinct().all()
    }
    if not watched_ids:
        return []

    watched = db.query(Movie).filter(Movie.tmdb_id.in_(watched_ids)).all()
    if not watched:
        return []

    model = get_model()
    index, indexed_ids = _get_index_and_ids()
    if index.ntotal == 0:
        return []

    vectors = model.encode([_movie_text(movie) for movie in watched]).astype("float32")
    distances, positions = index.search(vectors, min(index.ntotal, max(top_k * 3, 50)))
    watched_db_ids = {movie.id for movie in watched}
    best_distance = {}

    for distance_row, position_row in zip(distances, positions):
        for distance, position in zip(distance_row, position_row):
            if position < 0 or position >= len(indexed_ids):
                continue
            db_id = int(indexed_ids[position])
            if db_id in watched_db_ids:
                continue
            distance = float(distance)
            if db_id not in best_distance or distance < best_distance[db_id]:
                best_distance[db_id] = distance

    ranked_db_ids = sorted(best_distance, key=best_distance.get)[:top_k]
    rows = db.query(Movie.id, Movie.tmdb_id).filter(
        Movie.id.in_(ranked_db_ids)
    ).all()
    tmdb_by_db_id = {db_id: tmdb_id for db_id, tmdb_id in rows}
    return [tmdb_by_db_id[mid] for mid in ranked_db_ids if mid in tmdb_by_db_id]
