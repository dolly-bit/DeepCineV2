"""
Inference for the collaborative-filtering recommender trained by
train_collaborative_model.py.

Genuine collaborative filtering: a user's recommendation score for a movie
is just the dot product of two learned latent vectors (user_factors[u] .
item_factors[i]), estimated purely from the co-watch interaction matrix.
No title, overview, genre, or embedding is used anywhere in this file -
that's what makes it collaborative rather than content-based.

At inference time we only need numpy (not the `implicit` package), since
training already collapsed everything down to two small factor matrices.
"""

import pickle
from pathlib import Path

import numpy as np

from app.database.connection import SessionLocal
from app.models import Movie

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
MODEL_PATH = BASE_DIR / "cf_model.pkl"

_artifacts = None


def has_model() -> bool:
    return MODEL_PATH.exists()


def _load_artifacts():
    global _artifacts

    if _artifacts is None:
        with open(MODEL_PATH, "rb") as f:
            _artifacts = pickle.load(f)

    return _artifacts


def recommend_for_user(user_id: int, top_k: int = 10):
    """
    Returns a ranked list of Movie ORM objects for `user_id` using the
    trained ALS latent factors, or None if:
      - no model has been trained yet, or
      - the user has no watch history the model was trained on (cold start)

    Callers should treat None as "fall back to a different strategy",
    not as an error.
    """
    if not has_model():
        return None

    artifacts = _load_artifacts()
    user_to_idx = artifacts["user_to_idx"]

    if user_id not in user_to_idx:
        return None

    user_idx = user_to_idx[user_id]
    item_factors = artifacts["item_factors"]
    user_factors = artifacts["user_factors"]
    idx_to_item = artifacts["idx_to_item"]
    interaction_matrix = artifacts["interaction_matrix"]

    # Predicted affinity for every movie = dot product of latent vectors.
    scores = item_factors @ user_factors[user_idx]

    already_watched = set(interaction_matrix[user_idx].indices)

    ranked_item_indices = np.argsort(scores)[::-1]

    recommended_tmdb_ids = []
    for item_idx in ranked_item_indices:
        if item_idx in already_watched:
            continue

        recommended_tmdb_ids.append(idx_to_item[item_idx])

        if len(recommended_tmdb_ids) >= top_k:
            break

    if not recommended_tmdb_ids:
        return []

    db = SessionLocal()
    try:
        movies = (
            db.query(Movie)
            .filter(Movie.tmdb_id.in_(recommended_tmdb_ids))
            .all()
        )

        movie_by_tmdb_id = {m.tmdb_id: m for m in movies}

        # Preserve the model's ranking order (the DB query doesn't).
        ordered = [
            movie_by_tmdb_id[tmdb_id]
            for tmdb_id in recommended_tmdb_ids
            if tmdb_id in movie_by_tmdb_id
        ]

        return ordered
    finally:
        db.close()
