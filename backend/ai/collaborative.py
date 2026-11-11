"""Inference helpers for the ALS collaborative-filtering model."""
import pickle
from pathlib import Path

import numpy as np

from app.database.connection import SessionLocal
from app.models import Movie

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "cf_model.pkl"
_artifacts = None


def has_model() -> bool:
    return MODEL_PATH.exists()


def _load_artifacts():
    global _artifacts
    if _artifacts is None:
        with open(MODEL_PATH, "rb") as model_file:
            _artifacts = pickle.load(model_file)
    return _artifacts


def invalidate_model_cache():
    """Clear cached factors after a model retrain or artifact replacement."""
    global _artifacts
    _artifacts = None


def recommendation_scores_for_user(user_id: int, top_k: int = 100):
    """Return ranked (TMDB ID, ALS score) pairs, excluding watched items."""
    if not has_model() or top_k <= 0:
        return []

    artifacts = _load_artifacts()
    user_to_idx = artifacts["user_to_idx"]
    if user_id not in user_to_idx:
        return []

    user_idx = user_to_idx[user_id]
    factors = artifacts["item_factors"] @ artifacts["user_factors"][user_idx]
    already_watched = set(artifacts["interaction_matrix"][user_idx].indices)
    ranked = np.argsort(factors)[::-1]
    results = []

    for item_idx in ranked:
        item_idx = int(item_idx)
        if item_idx in already_watched:
            continue
        tmdb_id = artifacts["idx_to_item"].get(item_idx)
        score = float(factors[item_idx])
        if tmdb_id is None or not np.isfinite(score):
            continue
        results.append((int(tmdb_id), score))
        if len(results) >= top_k:
            break
    return results


def recommend_for_user(user_id: int, top_k: int = 10):
    """Return Movie ORM objects in ALS ranking order (legacy API contract)."""
    ranked = recommendation_scores_for_user(user_id, top_k=top_k)
    if not ranked:
        return None if not has_model() else []

    tmdb_ids = [tmdb_id for tmdb_id, _ in ranked]
    db = SessionLocal()
    try:
        movies = db.query(Movie).filter(Movie.tmdb_id.in_(tmdb_ids)).all()
        by_tmdb_id = {movie.tmdb_id: movie for movie in movies}
        return [by_tmdb_id[mid] for mid in tmdb_ids if mid in by_tmdb_id]
    finally:
        db.close()
