import numpy as np
from pathlib import Path

from app.database.connection import SessionLocal
from app.models.movie import Movie


BASE_DIR = Path(__file__).resolve().parent.parent

# Everything ML-related (faiss, sentence-transformers/torch) is imported
# lazily, on first actual use, instead of at module import time.
#
# Why this matters: this module is imported by app.routes.recommend, which
# is wired up in app.main at server startup. If `faiss` and, worse,
# `sentence-transformers` (which pulls in torch) were imported here at
# module scope, every single app boot - including cold starts on a free
# hosting tier - would pay the full cost of loading torch before the
# server could accept a single request. That's the #1 cause of the slow
# backend boot. Deferring these imports to the first call to
# recommend_movies() means the server starts accepting requests
# immediately, and only pays the ML-loading cost once, lazily, on the
# first content-based recommendation request (subsequent calls reuse the
# cached model/index below).

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


def recommend_movies(movie_name: str, top_k: int = 10):

    db = SessionLocal()

    try:
        movie = (
            db.query(Movie)
            .filter(Movie.title.ilike(f"%{movie_name}%"))
            .first()
        )

        if not movie:
            return []

        text = f"""
        Title: {movie.title}
        Overview: {movie.overview or ""}
        Language: {movie.original_language or ""}
        """

        # Load model + faiss index only when a recommendation is requested
        model_instance = get_model()
        index, movie_ids = _get_index_and_ids()

        embedding = model_instance.encode(
            [text]
        ).astype("float32")

        _, indices = index.search(
            embedding,
            top_k + 1
        )

        recommendations = []

        for idx in indices[0]:

            if idx < 0 or idx >= len(movie_ids):
                continue

            movie_id = int(movie_ids[idx])

            if movie_id == movie.id:
                continue

            rec_movie = (
                db.query(Movie)
                .filter(Movie.id == movie_id)
                .first()
            )

            if rec_movie:
                recommendations.append({
                    "id": rec_movie.id,
                    "title": rec_movie.title,
                    "poster_url": (
                        f"https://image.tmdb.org/t/p/w500"
                        f"{rec_movie.poster_path}"
                        if rec_movie.poster_path
                        else None
                    ),
                    "overview": rec_movie.overview,
                    "rating": rec_movie.vote_average,
                    "release_date": rec_movie.release_date,
                })

        return recommendations[:top_k]

    finally:
        db.close()